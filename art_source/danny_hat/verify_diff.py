"""Strict check: compare before/ backups with the live files - every changed pixel must be a hat pixel whose
old colour maps to the new one, and alpha must stay 0/255."""
import os
import sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'le_src')))
from pngio import read_png
import recolour_hat as R

bad = 0
for spec in R.FILES:
    name = spec['name']
    W0, H0, a = read_png(os.path.join('before', name))
    W1, H1, b = read_png(os.path.join(R.DANNY, name))
    assert (W0, H0) == (W1, H1), (name, W0, H0, W1, H1)
    mask = R.enclosed(a, spec['box'])
    changed, outside_mask, wrong_map, alphas = 0, 0, 0, set()
    for y in range(H0):
        for x in range(W0):
            p, q = tuple(a[y][x]), tuple(b[y][x])
            alphas.add(q[3])
            if p == q:
                continue
            changed += 1
            if (x, y) not in mask:
                outside_mask += 1
            elif R.MAP.get(R.key(p)) != R.key(q):
                wrong_map += 1
    status = 'OK' if (outside_mask == 0 and wrong_map == 0 and alphas <= {0, 255}) else 'FAIL'
    bad += status == 'FAIL'
    print('%-22s changed=%-5d outside_hat=%d wrong_mapping=%d alphas=%s %s' % (name, changed, outside_mask, wrong_map, sorted(alphas), status))
sys.exit(1 if bad else 0)
