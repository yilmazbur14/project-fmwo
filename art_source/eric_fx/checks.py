import sys
from pngio import read_png
SHEETS = [('eric_thrown_sword.png', 96, 96, 8), ('eric_sword_planted.png', 64, 96, 2),
          ('eric_leap_shadow.png', 48, 16, 3), ('eric_quake_impact.png', 160, 80, 6),
          ('eric_quake_segment.png', 32, 32, 4)]
base = sys.argv[1] if len(sys.argv) > 1 else './'
for name, fw, fh, n in SHEETS:
    w, h, px = read_png(base + name)
    assert (w, h) == (fw * n, fh), (name, w, h)
    alphas = sorted({p[3] for row in px for p in row})
    cols = {p for row in px for p in row if p[3]}
    edges = []
    for i in range(n):
        f = [row[i * fw:(i + 1) * fw] for row in px]
        e = {'top': any(p[3] for p in f[0]), 'bottom': any(p[3] for p in f[-1]),
             'left': any(r[0][3] for r in f), 'right': any(r[-1][3] for r in f)}
        edges.append(''.join(k[0] for k, v in e.items() if v) or '-')
    print(f'{name:28s} {w}x{h} frames={n} alphas={alphas} colours={len(cols)} edge-touch per frame={edges}')
