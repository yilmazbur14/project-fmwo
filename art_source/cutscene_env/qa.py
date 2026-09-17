from pngio import read_png
from lib import RGB2KEY
D = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Cutscenes/Intro/'
spec = {
    'street_sky.png': (960, 360, True),
    'street_buildings.png': (1280, 360, False),
    'street_fg.png': (1280, 360, False),
    'poster_closeup.png': (640, 360, True),
    'rain_overlay.png': (2560, 360, False),
    'sign_flicker.png': (63, 70, True),
}
for name, (w0, h0, opaque) in spec.items():
    w, h, p = read_png(D + name)
    assert (w, h) == (w0, h0), (name, w, h)
    alphas = set(px[3] for row in p for px in row)
    assert alphas <= {0, 255}, (name, alphas)
    cols = set(px[:3] for row in p for px in row if px[3] == 255)
    bad = [c for c in cols if c not in RGB2KEY]
    assert not bad, (name, bad[:5])
    transparent = sum(1 for row in p for px in row if px[3] == 0)
    if opaque:
        assert transparent == 0, (name, transparent)
    extra = ''
    if name == 'street_buildings.png':
        # ground band must be solid for the whole width
        holes = [(x, y) for y in range(186, 360) for x in range(w) if p[y][x][3] == 0 and not (373 <= x <= 452 and y < 238)]
        assert not holes, holes[:5]
        tops = []
        for x0, x1 in ((0, 196), (197, 372), (453, 700), (701, 858), (859, 1076), (1077, 1279)):
            ys = [min(y for y in range(h) if p[y][x][3]) for x in range(x0, x1 + 1)]
            tops.append((x0, x1, min(ys), max(ys)))
        extra = ' rooftop rows %s' % tops
    print('%-22s %4dx%-3d alpha%s colours=%2d transparent=%d%s' % (name, w, h, sorted(alphas), len(cols), transparent, extra))
print('QA ok')
