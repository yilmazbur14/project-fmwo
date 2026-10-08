"""Checks on the WRITTEN files in rider/ (reads only): the identity frames, and the ride f0 recomposing
the approved mounted idle with the kaiju and fx layers."""
import os
import sys
sys.dont_write_bytecode = True
import jr_common as C
from PIL import Image

R = C.RIDER
ok = True
def frame(name, i):
    return Image.open(os.path.join(R, name + '.png')).convert('RGBA').crop((96 * i, 0, 96 * i + 96, 96))

ref = Image.open(os.path.join(R, 'ref', 'kaiju_mounted_idle_rider.png')).convert('RGBA')
crop = ref.crop((83, -10, 179, 86))
d = C.pixel_diff(frame('jordan_ride_idle', 0), crop); print('ride_idle f0 == approved rider layer crop (83,-10):', d or 'IDENTICAL'); ok &= not d
k = Image.open(os.path.join(R, 'ref', 'kaiju_mounted_idle_kaiju.png')).convert('RGBA')
fx = Image.open(os.path.join(R, 'ref', 'kaiju_mounted_idle_fx.png')).convert('RGBA')
comp = k.copy(); comp.alpha_composite(fx)
pad = Image.new('RGBA', (k.width, k.height + 10), (0, 0, 0, 0)); pad.alpha_composite(comp, (0, 10))
pad.alpha_composite(frame('jordan_ride_idle', 0), (83, 0))
comp2 = pad.crop((0, 10, k.width, k.height + 10))
appr = Image.open(os.path.join(C.APPROVAL, 'kaiju_mounted_idle.png')).convert('RGBA')
d = C.pixel_diff(comp2, appr); print('kaiju + fx + ride_idle f0 (SEAT on RIDER_SEAT) == approved kaiju_mounted_idle.png:', d or 'IDENTICAL'); ok &= not d
for i in (3, 4, 5):
    d = C.pixel_diff(frame('jordan_butt_land', i), C.live_sheet('jordan_defeat').crop((96 * i, 0, 96 * i + 96, 96)))
    print('butt_land f%d == live jordan_defeat f%d:' % (i, i), d or 'IDENTICAL'); ok &= not d
d = C.pixel_diff(frame('jordan_box_open', 0), C.live_sheet('jordan_idle').crop((0, 0, 96, 96)))
print('box_open f0 == live jordan_idle f0:', d or 'IDENTICAL'); ok &= not d
sys.exit(0 if ok else 1)
