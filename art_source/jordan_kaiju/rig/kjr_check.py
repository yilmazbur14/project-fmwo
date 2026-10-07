"""Check: the rig's rest frame equals the approved kaiju layer (shifted to the new frame)."""
import sys
sys.dont_write_bytecode = True
import kj_common as K, kjr as R, kjr_render as RR
import kj_frames2 as F2, kj_export as X


def approved_kaiju():
    final, afx, L = F2.layers(False)
    ap = X.to_frame(L['kaiju'])
    dx, dy = R.FEET[0] - 86, R.FEET[1] - 218
    return {(x + dx, y + dy): k for (x, y), k in ap.items()}


def check(px=None):
    if px is None:
        px, fx, info = RR.render_body()
    ap = approved_kaiju()
    a, b = set(ap.items()), set(px.items())
    return len(a - b), len(b - a), sorted(set(q for q, k in (a ^ b)))


if __name__ == '__main__':
    na, nb, d = check()
    print('only approved', na, 'only new', nb, d[:20])
