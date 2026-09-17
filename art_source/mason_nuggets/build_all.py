"""Build every deliverable PNG into ./out and run the contract checks."""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/'
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

def run(args, cwd=HERE):
    r = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr)
        raise SystemExit('failed: %s' % args)

run(['build_sheet.py', PROJ + 'mason_sheet.png', os.path.join(OUT, 'mason_sheet.png')], cwd=os.path.join(HERE, 'rig'))
run(['meteor.py', os.path.join(OUT, 'nugget_meteor.png')])
run(['target.py', os.path.join(OUT, 'nugget_target.png')])
run(['impact.py', os.path.join(OUT, 'nugget_impact.png')])
run(['elbow_v2.py', os.path.join(OUT, 'elbow_target_v2.png'), os.path.join(OUT, 'elbow_impact_v2.png')])

CONTRACT = {
    'mason_sheet.png': (64, 64, 19),
    'nugget_meteor.png': (48, 64, 4),
    'nugget_target.png': (48, 26, 4),
    'nugget_impact.png': (64, 48, 5),
    'elbow_target_v2.png': (76, 76, 2),
    'elbow_impact_v2.png': (104, 104, 4),
}
ok = True
for name, (fw, fh, n) in CONTRACT.items():
    w, h, px = read_png(os.path.join(OUT, name))
    alphas = sorted({p[3] for row in px for p in row})
    good = (w, h) == (fw * n, fh) and set(alphas) <= {0, 255}
    edge = 0
    for i in range(n):
        for y in range(fh):
            for x in range(fw):
                if px[y][i * fw + x][3] and (x in (0, fw - 1) or y in (0, fh - 1)):
                    edge += 1
    print('%-22s %4dx%-4d frames %2d x %dx%d  alphas %s  edge-touch px %d  %s' % (
        name, w, h, n, fw, fh, alphas, edge, 'OK' if good else 'FAIL'))
    ok &= good
# frames 0-14 untouched
_, _, a = read_png(PROJ + 'mason_sheet.png')
_, _, b = read_png(os.path.join(OUT, 'mason_sheet.png'))
diff = sum(1 for y in range(64) for x in range(960) if tuple(a[y][x]) != tuple(b[y][x]))
print('mason_sheet frames 0-14 vs shipped: %d differing px' % diff)
ok &= diff == 0
print('ALL CHECKS PASS' if ok else 'CHECKS FAILED')
