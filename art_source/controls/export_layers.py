"""Build final PNGs + per-layer PNGs (for layered .aseprite files) and verify them."""
import os
import bg
import common
from common import Canvas, write_png, read_png, validate_png, DB32
import keys_final
from keys import COL, orient
from cmp2 import body_variant

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(HERE, 'final')
LAY = os.path.join(HERE, 'layers')
os.makedirs(FIN, exist_ok=True)
os.makedirs(LAY, exist_ok=True)


class RecCanvas(Canvas):
    """Canvas that remembers, per layer group, the last colour each group wrote to each pixel."""
    def __init__(self, w, h):
        super().__init__(w, h)
        self.group = None
        self.writes = {}

    def set(self, x, y, c):
        super().set(x, y, c)
        if self.group is not None and 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.writes.setdefault(self.group, {})[(x, y)] = c


def layer_png(rc, group, path):
    lc = Canvas(rc.w, rc.h)
    for (x, y), col in rc.writes.get(group, {}).items():
        lc.p[y][x] = col
    lc.save(path)
    return lc


def composite(layers, w, h):
    out = Canvas(w, h)
    for lc in layers:
        for y in range(h):
            for x in range(w):
                if lc.p[y][x] is not None:
                    out.p[y][x] = lc.p[y][x]
    return out


def same(a, b):
    return all(a.p[y][x] == b.p[y][x] for y in range(a.h) for x in range(a.w))


# ------------------------------------------------ background
BG_GROUPS = [
    ('room', [bg.draw_wall, bg.draw_floor, bg.draw_door_spill]),
    ('lockers_bench', [bg.draw_lockers, bg.draw_bench]),
    ('door_banner', [bg.draw_door, bg.draw_banner]),
    ('props', [bg.draw_clock, bg.draw_towel, bg.draw_gloves]),
    ('lights', [lambda c: [bg.draw_fixture(c, fx) for fx in bg.FIXTURES]]),
]
rc = RecCanvas(bg.W, bg.H)
for name, fns in BG_GROUPS:
    rc.group = name
    for fn in fns:
        fn(rc)
reference = bg.build()
assert same(rc, reference), 'recorded draw differs from bg.build()'
assert all(rc.p[y][x] is not None for y in range(rc.h) for x in range(rc.w)), 'background has transparent pixels'
rc.save(os.path.join(FIN, 'controls_bg.png'))
bg_layers = [layer_png(rc, name, os.path.join(LAY, 'bg_%d_%s.png' % (i, name))) for i, (name, _) in enumerate(BG_GROUPS)]
assert same(composite(bg_layers, bg.W, bg.H), rc), 'bg layers do not composite to final'
used = sorted(set(rc.p[y][x] for y in range(rc.h) for x in range(rc.w)))
print('bg ok: %d DB32 colours used: %s' % (len(used), ' '.join('#' + u for u in used)))

# ------------------------------------------------ keys (keycap layer + legend layer)
def key_layers(glyph, body_w=None):
    body = Canvas(32, 32)
    body.grid(0, 0, [''.join(r) for r in body_variant(keys_final.BODY)], COL)
    legend = Canvas(32, 32)
    gh, gw = len(glyph), len(glyph[0])
    bw = body_w or gw
    x0 = int(round(15.5 - bw / 2 + 0.5))
    y0 = int(round(12.5 - gh / 2 + 0.5))
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == 'X':
                legend.set(x0 + i, y0 + j, COL['g'])
    return body, legend


kq, kw, karrows = keys_final.build()
for name, final, glyph, bw in [('key_q', kq, keys_final.Q, 14), ('key_w', kw, keys_final.W, None)]:
    body, legend = key_layers(glyph, bw)
    assert same(composite([body, legend], 32, 32), final)
    final.save(os.path.join(FIN, name + '.png'))
    body.save(os.path.join(LAY, name + '_0_keycap.png'))
    legend.save(os.path.join(LAY, name + '_1_legend.png'))

arr_body = Canvas(96, 64)
arr_leg = Canvas(96, 64)
for d, (ox, oy) in [('up', (32, 0)), ('left', (0, 32)), ('down', (32, 32)), ('right', (64, 32))]:
    b, l = key_layers(orient(keys_final.ARROW, d))
    arr_body.blit(b, ox, oy)
    arr_leg.blit(l, ox, oy)
assert same(composite([arr_body, arr_leg], 96, 64), karrows)
karrows.save(os.path.join(FIN, 'key_arrows.png'))
arr_body.save(os.path.join(LAY, 'key_arrows_0_keycaps.png'))
arr_leg.save(os.path.join(LAY, 'key_arrows_1_arrows.png'))

# transparency check: outside key silhouettes must be alpha 0, inside fully opaque
for name, (w, h) in [('key_q', (32, 32)), ('key_w', (32, 32)), ('key_arrows', (96, 64))]:
    W_, H_, px = read_png(os.path.join(FIN, name + '.png'))
    assert (W_, H_) == (w, h)
    alphas = set(p[3] for row in px for p in row)
    assert alphas <= {0, 255}, alphas
    # corners of every 32x32 cell must be transparent
    for cy in range(0, h, 32):
        for cx in range(0, w, 32):
            for (x, y) in [(0, 0), (31, 0), (0, 31), (31, 31), (2, 1), (1, 2)]:
                assert px[cy + y][cx + x][3] == 0, (name, cx + x, cy + y)
    # empty cells of the arrow cluster (top-left, top-right) must be fully transparent
    if name == 'key_arrows':
        for (cx, cy) in [(0, 0), (64, 0)]:
            assert all(px[cy + y][cx + x][3] == 0 for y in range(32) for x in range(32)), ('cell not empty', cx, cy)
print('keys ok')
print('final:', sorted(os.listdir(FIN)))
print('layers:', sorted(os.listdir(LAY)))
