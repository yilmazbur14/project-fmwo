"""Write final PNGs + per-layer PNGs for the layered .aseprite files, and verify the layers composite back."""
import os
from lib import Canvas
import street, street2, poster, sky, fg, overlays

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
LAY = os.path.join(HERE, 'layers')
os.makedirs(LAY, exist_ok=True)


def diff_layer(full, under):
    d = Canvas(full.w, full.h)
    for y in range(full.h):
        for x in range(full.w):
            if full.p[y][x] != under.p[y][x]:
                d.p[y][x] = full.p[y][x]
    return d


def composite(layers):
    out = Canvas(layers[0].w, layers[0].h)
    for l in layers:
        out.blit(l, 0, 0)
    return out


def same(a, b):
    return a.w == b.w and a.h == b.h and all(a.p[y][x] == b.p[y][x] for y in range(a.h) for x in range(a.w))


def check_alpha_and_holes(c, name, opaque):
    holes = sum(1 for row in c.p for k in row if k is None)
    if opaque:
        assert holes == 0, (name, 'has transparent pixels', holes)
    return holes


# ---- sky
s = sky.build()
s.save(os.path.join(OUT, 'street_sky.png'))
check_alpha_and_holes(s, 'sky', True)

# ---- street (layers: street, poster)
street2.OPTS['poster'] = True
full = street2.build()
street2.OPTS['poster'] = False
nopost = street2.build()
street2.OPTS['poster'] = True
post_layer = diff_layer(full, nopost)
assert same(composite([nopost, post_layer]), full)
full.save(os.path.join(OUT, 'street_buildings.png'))
nopost.save(os.path.join(LAY, 'street_buildings__street.png'))
post_layer.save(os.path.join(LAY, 'street_buildings__poster.png'))

# ---- foreground props
f = fg.build()
f.save(os.path.join(OUT, 'street_fg.png'))

# ---- poster close-up (layers: wall, flyers, poster, lettering)
poster.OPTS['lettering'] = True
pc = poster.build()
wall_l = poster.LAYERS['wall']
flyers_full = poster.LAYERS['flyers']
poster.OPTS['lettering'] = False
blank = poster.build()
poster.OPTS['lettering'] = True
fly_l = diff_layer(flyers_full, wall_l)
pos_l = diff_layer(blank, flyers_full)
let_l = diff_layer(pc, blank)
assert same(composite([wall_l, fly_l, pos_l, let_l]), pc)
check_alpha_and_holes(pc, 'poster', True)
pc.save(os.path.join(OUT, 'poster_closeup.png'))
for nm, l in (('wall', wall_l), ('flyers', fly_l), ('poster', pos_l), ('lettering', let_l)):
    l.save(os.path.join(LAY, 'poster_closeup__%s.png' % nm))

# ---- overlays
strip, frames = overlays.rain_strip()
strip.save(os.path.join(OUT, 'rain_overlay.png'))
for i, fr in enumerate(frames):
    fr.save(os.path.join(LAY, 'rain_f%d.png' % i))
sstrip, sframes = overlays.sign_strip()
sstrip.save(os.path.join(OUT, 'sign_flicker.png'))
for i, fr in enumerate(sframes):
    fr.save(os.path.join(LAY, 'sign_f%d.png' % i))
print('layers ok')
