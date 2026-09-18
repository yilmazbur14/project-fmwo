"""Render every review deliverable for Danny's transformation design pass.

  danny_transformation.gif    the whole sequence at the proposed timings
  danny_evolution_flash.gif   just the FireRed-style flash
  danny_keys_6x.png           contact sheet of every key at 6x
  mockup_sumo_1920.png        the evolved form in the real arena, player for scale
  mockup_tiny_1920.png        tiny Danny in the same ring at the same scale

Usage: python make_previews.py <output-dir> [<arena-plate.png>]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pngio import read_png, write_png, upscale     # noqa: E402
from rig import to_pix                              # noqa: E402
import danny_small as SM                            # noqa: E402
import danny_honda as SU                             # noqa: E402
import transform as T                               # noqa: E402

# --- where the sprites stand in the 1920x1080 arena --------------------------
GROUND_Y = 924          # the player's feet in ArenaScene
BOSS_CX = 1210
PLAYER_POS = (959, 900)  # the MainPlayer node position in ArenaScene
BOSS_SCALE = 3
PLAYER_SCALE = 2


def blit(dst, src, ox, oy, scale=1):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for k in range(scale):
            ty = oy + y * scale + k
            if not (0 <= ty < H):
                continue
            for x, p in enumerate(row):
                if not p[3]:
                    continue
                for j in range(scale):
                    tx = ox + x * scale + j
                    if 0 <= tx < W:
                        dst[ty][tx] = p


def contact_sheet(path, scale=6):
    """Every distinct pose at `scale`: the small-form keys on top, the three
    evolved registers beneath, then the two flash silhouettes at the shared
    anchor."""
    small = [(k, to_pix(SM.build(k))) for k in SM.KEYS]
    big = [(p, to_pix(SU.build(p))) for p in ('idle', 'awake', 'land')]
    sil = [('sil_small', T.silhouette(T.small_in_big('flex_in'))),
           ('sil_big', T.silhouette(T.sumo_in_big('awake')))]

    sc = 64 * scale
    bc, br = SU.W * scale, SU.H * scale
    cols_s, cols_b = 5, 3
    rows_s = (len(small) + cols_s - 1) // cols_s
    Wp = max(cols_s * sc, cols_b * bc)
    Hp = rows_s * sc + br + T.BH * scale
    px = [[(26, 24, 38, 255)] * Wp for _ in range(Hp)]

    for i, (k, p) in enumerate(small):
        blit(px, p, (i % cols_s) * sc, (i // cols_s) * sc, scale)
    for i, (k, p) in enumerate(big):
        blit(px, p, i * bc, rows_s * sc, scale)
    for i, (k, p) in enumerate(sil):
        blit(px, p, i * T.BW * scale, rows_s * sc + br, scale)

    for i in range(1, cols_s):
        for y in range(rows_s * sc):
            px[y][i * sc] = (70, 66, 90, 255)
    for i in range(1, cols_b):
        for y in range(rows_s * sc, rows_s * sc + br):
            px[y][i * bc] = (70, 66, 90, 255)
    for y in [r * sc for r in range(1, rows_s)] +              [rows_s * sc, rows_s * sc + br]:
        for x in range(Wp):
            px[y][x] = (70, 66, 90, 255)
    write_png(path, Wp, Hp, px)
    print('  ', os.path.basename(path), Wp, 'x', Hp)


def sheet_contact(path, scale=2, wrap=5):
    """Every production sheet, one per row (wrapped at `wrap` frames)."""
    import sheets as SHEETS
    built = SHEETS.build_all()
    order = ['danny_walk', 'danny_grip', 'danny_tear', 'danny_flex',
             'danny_sumo_evolve', 'danny_sumo_idle', 'danny_sumo_wake',
             'danny_sumo_slap', 'danny_sumo_step', 'danny_sumo_hit',
             'danny_sumo_defeat']
    rows = []
    for name in order:
        px, fw, fh, meta = built[name]
        n = len(meta['frames'])
        for r in range(0, n, wrap):
            rows.append((px, fw, fh, r, min(wrap, n - r)))
    Wp = max(cnt * fw for (_, fw, _, _, cnt) in rows) * scale
    Hp = sum(fh for (_, _, fh, _, _) in rows) * scale
    out = [[(26, 24, 38, 255)] * Wp for _ in range(Hp)]
    y0 = 0
    for (px, fw, fh, start, cnt) in rows:
        for y in range(fh):
            for k in range(scale):
                ty = y0 + y * scale + k
                for x in range(cnt * fw):
                    p = px[y][(start * fw) + x]
                    if p[3]:
                        for j in range(scale):
                            out[ty][x * scale + j] = p
        y0 += fh * scale
        if y0 < Hp:
            for x in range(Wp):
                out[y0 - 1][x] = (70, 66, 90, 255)
    write_png(path, Wp, Hp, out)
    print('  ', os.path.basename(path), Wp, 'x', Hp, len(rows), 'rows')


def mockup(path, plate_path, which):
    w, h, plate = read_png(plate_path)
    px = [row[:] for row in plate]
    # the player, exactly as ArenaScene places him
    pw, ph, sheet = read_png(T.PLAYER_SHEET)
    pl = [[sheet[y][x] for x in range(32)] for y in range(32)]
    blit(px, pl, PLAYER_POS[0] - 16 * PLAYER_SCALE,
         PLAYER_POS[1] - 16 * PLAYER_SCALE, PLAYER_SCALE)
    if which == 'sumo':
        sp = to_pix(SU.build('idle'))
        fw, fh = SU.W, SU.H
    else:
        sp = T.small_in_big('arrive')
        fw, fh = T.BW, T.BH
    blit(px, sp, BOSS_CX - (fw * BOSS_SCALE) // 2,
         GROUND_Y - fh * BOSS_SCALE, BOSS_SCALE)
    write_png(path, w, h, px)
    print('  ', os.path.basename(path), w, 'x', h)


if __name__ == '__main__':
    out = sys.argv[1]
    plate = sys.argv[2] if len(sys.argv) > 2 else None
    os.makedirs(out, exist_ok=True)
    print('rendering previews into', out)
    T.render_gif(os.path.join(out, 'danny_transformation.gif'), T.beats(),
                 scale=2)
    T.render_gif(os.path.join(out, 'danny_evolution_flash.gif'),
                 T.flash_beats(), scale=2)
    contact_sheet(os.path.join(out, 'danny_keys_6x.png'))
    sheet_contact(os.path.join(out, 'danny_sheets_2x.png'))
    if plate:
        mockup(os.path.join(out, 'mockup_sumo_1920.png'), plate, 'sumo')
        mockup(os.path.join(out, 'mockup_tiny_1920.png'), plate, 'tiny')
    b = T.beats()
    print('sequence: %d frames, %d ms total' % (len(b), sum(x[2] for x in b)))
