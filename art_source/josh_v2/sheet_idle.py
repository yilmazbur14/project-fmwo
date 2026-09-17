"""Idle frames 0-2, built as tagged layers so the upper body can breathe while the feet stay locked."""
from jlib import *
import idle as I
import parts as P
import head as HD
import patch_idle

TH_LIMB = [0.0, 0.35, 0.6, 0.85, 0.98]
G = I.G


def layer():
    return blank()


def idle_layers(eyes='B', mouth='grin'):
    L = []
    # lower body (locked)
    c = layer(); I.hf_shade(c, poly_mask(G['n_leg']), lambda px, py: I.hcap(px, py, 25, 48, 23, 57, 6.5, 5.5), I.SKIN, TH_LIMB); L.append(('lower', c))
    c = layer(); I.hf_shade(c, poly_mask(G['f_leg']), lambda px, py: I.hcap(px, py, 41, 48, 44, 57, 6.0, 5.2), I.SKIN, TH_LIMB); L.append(('lower', c))
    c = layer(); I.draw_boot(c, G['n_boot'], shaft=(16, 29), toe=(14, 61)); L.append(('lower', c))
    c = layer(); I.draw_boot(c, G['f_boot'], shaft=(38, 50), toe=(52, 61)); L.append(('lower', c))
    # torso
    c = layer(); bm = poly_mask(G['body'])
    I.hf_shade(c, bm, I.torso_h, I.SKIN, [0.05, 0.4, 0.66, 0.88, 0.985], crease=3, crease_th=1.1, zscale=0.9)
    despeckle(c, region=bm); L.append(('upper', c))
    c = layer(); block(c, *P.SPEEDO); L.append(('lower', c))
    # far arm + hip fist
    c = layer(); I.hf_shade(c, poly_mask(G['f_upper']), lambda px, py: max(I.hcap(px, py, 50, 29, 54, 40, 5, 3.8), I.hdome(px, py, 50, 30, 4.5, 5, 5)), I.SKIN, TH_LIMB); L.append(('upper', c))
    c = layer(); I.hf_shade(c, poly_mask(G['f_fore']), lambda px, py: I.hcap(px, py, 54, 41, 48, 47, 3.5, 3.0), I.SKIN, TH_LIMB); L.append(('upper', c))
    c = layer(); block(c, *P.FAR_FIST); L.append(('upper', c))

    def n_up_h(px, py):
        h = I.hcap(px, py, 15, 30, 7, 31, 5.5, 4.5)
        h = max(h, I.hdome(px, py, 12, 26.5, 5.5, 5, 6))
        h = max(h, I.hdome(px, py, 15, 30.5, 5.5, 5.5, 5.5))
        return h
    c = layer(); I.hf_shade(c, poly_mask(G['n_upper']), n_up_h, I.SKIN, TH_LIMB); L.append(('upper', c))
    c = layer(); I.hf_shade(c, poly_mask(G['n_fore']), lambda px, py: I.hcap(px, py, 7, 30, 10, 17, 4.0, 3.2), I.SKIN, TH_LIMB); L.append(('pump', c))
    c = layer(); block(c, *P.NEAR_FIST); L.append(('pump', c))
    c = layer(); HD.build_head(c, eyes, mouth); L.append(('head', c))
    return L


BICEP_PATCH_ROWS = (24, 32)   # patches in this y-range belong to the bicep


def build_idle(dy_upper=0, pump=0, dy_head=None, eyes='B', mouth='grin', extra=None):
    """dy_upper: upper body offset (+ = down). pump: extra offset for near forearm+fist (- = up).
    Feet/legs/speedo never move."""
    if dy_head is None:
        dy_head = dy_upper
    offs = {'lower': 0, 'upper': dy_upper, 'pump': dy_upper + pump, 'head': dy_head}
    c = blank()
    for tag, lay in idle_layers(eyes, mouth):
        composite(c, shift_canvas(lay, 0, offs[tag]) if offs[tag] else lay)
    assert all(ch == '.' for ch in c[63]), 'row 63 not empty before shift'
    c = [['.'] * W] + c[:63]
    for (x, y, rows) in patch_idle.PATCHES:
        block(c, x, y + dy_upper, rows)
    if extra:
        extra(c)
    return c


if __name__ == '__main__':
    base = build_idle()
    ref = from_text(open(os.path.join(HERE, 'frozen', 'idle_approved.txt')).read())
    diff = sum(1 for y in range(H) for x in range(W) if base[y][x] != ref[y][x])
    print('layered F0 vs approved diff:', diff)
