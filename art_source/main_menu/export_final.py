"""Write the deliverable PNGs + per-layer / per-frame PNGs (inputs for the .aseprite files) into final/."""
import os
from lib import *
import bg, logo, fx, slider

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(HERE, 'final')
os.makedirs(os.path.join(FIN, 'layers'), exist_ok=True)
os.makedirs(os.path.join(FIN, 'fx_frames'), exist_ok=True)

comp, parts = bg.build()
assert all(comp.p[y][x] is not None for y in range(bg.H) for x in range(bg.W)), 'bg must be fully opaque'
comp.save(os.path.join(FIN, 'main_menu_bg.png'))
chk = Canvas(bg.W, bg.H)
for i, (name, lc) in enumerate(parts):
    lc.save(os.path.join(FIN, 'layers', '%d_%s.png' % (i, name)))
    chk.blit(lc, 0, 0)
assert chk.p == comp.p, 'layers do not composite to the final bg'
print('bg layers:', [n for n, _ in parts])

t = logo.crop_to_content(logo.render())
t.save(os.path.join(FIN, 'main_menu_title.png'))
print('title', t.w, t.h)

comp2, frames = fx.build()
assert comp2.p == comp.p
strip = Canvas(bg.W * fx.N, bg.H)
for i, fr in enumerate(frames):
    fr.save(os.path.join(FIN, 'fx_frames', 'f%02d.png' % i))
    strip.blit(fr, i * bg.W, 0)
strip.save(os.path.join(FIN, 'main_menu_bg_fx.png'))
used = sorted(set(comp.p[y][x] for y in range(bg.H) for x in range(bg.W)))
print('bg colours (%d):' % len(used), ' '.join(used))

for name, c in slider.build().items():
    if name != 'menu_slider_grabber':
        slider.check_nine_slice(c, slider.MARGINS)
    c.save(os.path.join(FIN, name + '.png'))
    slider.scale3(c).save(os.path.join(FIN, name + '_3x.png'))
print('slider textures written')
