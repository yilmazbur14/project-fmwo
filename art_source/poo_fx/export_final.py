"""Write the locked deliverables pixel-exact from the final grids + per-frame PNGs for Aseprite."""
import hashlib
import fxpng
import bomb_final
import explo_final

MASON = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/'


def strip(frames, fw, fh, pal):
    out = [[(0, 0, 0, 0)] * (fw * len(frames)) for _ in range(fh)]
    for i, g in enumerate(frames):
        assert len(g) == fh and all(len(r) == fw for r in g)
        for y in range(fh):
            for x in range(fw):
                c = pal[g[y][x]]
                if c:
                    out[y][i * fw + x] = fxpng.hexc(c)
    return out


jobs = [
    ('poo_bomb', bomb_final.build(20), 32, 32, bomb_final.PAL, (64, 32)),
    ('poo_explosion', explo_final.build(), 48, 48, explo_final.PAL, (240, 48)),
]
for name, frames, fw, fh, pal, size in jobs:
    px = strip(frames, fw, fh, pal)
    W, H = fw * len(frames), fh
    assert (W, H) == size, (name, W, H)
    fxpng.write_png(MASON + name + '.png', W, H, px)
    fxpng.write_png('out/%s_strip.png' % name, W, H, px)
    for i in range(len(frames)):
        fr = [row[i * fw:(i + 1) * fw] for row in px]
        fxpng.write_png('out/%s_f%d.png' % (name, i), fw, fh, fr)
    w2, h2, back = fxpng.read_png(MASON + name + '.png')
    assert (w2, h2) == size and back == [list(r) for r in px] or all(tuple(back[y][x]) == tuple(px[y][x]) for y in range(h2) for x in range(w2))
    cols = {}
    for row in px:
        for p in row:
            if p[3]:
                k = '#%02X%02X%02X' % p[:3]
                cols[k] = cols.get(k, 0) + 1
    sha = hashlib.sha256(open(MASON + name + '.png', 'rb').read()).hexdigest()[:16]
    print(name, 'size %dx%d' % (w2, h2), 'frames', len(frames), 'colours', len(cols), 'sha', sha)
    print('   ', sorted(cols.items(), key=lambda kv: -kv[1]))
