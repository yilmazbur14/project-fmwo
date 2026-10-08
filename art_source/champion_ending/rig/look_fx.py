import sys, os
sys.dont_write_bytecode = True
from PIL import Image
from common import zoom, save
import fx_screen as F
bg = Image.open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'cap', 'bg_cheer3.png')).convert('RGBA')
cb = F.confetti_burst(); sp = F.spot_sweep(); fl = F.lift_flash(); rn = F.confetti_rain()
picks = [('burst2', cb[2]), ('burst6', cb[6]), ('burst14', cb[14]), ('burst27', cb[27]),
         ('rain0', rn[0]), ('spot3', sp[3]), ('spot8', sp[8]), ('flash0', fl[0])]
out = Image.new('RGBA', (640 * 2, 360 * 4))
for i, (n, f) in enumerate(picks):
    c = bg.copy(); c.alpha_composite(f)
    out.paste(c, ((i % 2) * 640, (i // 2) * 360))
save(out, 'work/look_fx.png')
