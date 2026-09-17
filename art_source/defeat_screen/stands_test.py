import sys
from lib import *
import stands2, scene, props
import compose as cp
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 4
st = stands2.to_img(stands2.build_stands(seed))
st.save('out/stands2_only.png')
im = st.copy()
scene.canvas(im); scene.ropes_side(im); scene.ropes_far(im); scene.posts(im)
pimg, union = cp.player_layer()
ox, oy = cp.PLAYER_AT
cp.cast_shadow(im, union, ox, oy)
for (x, y) in union | outline_of(union):
    c = pimg.get(x, y)
    if c is not None:
        im.set(ox + x, oy + y, c)
props.apply_shadow(im, props.boss_shadow_mask(522, 178, 1.75, 1.9, 0.25))
props.pennant(im, 20, 6, 52, 64, props.pennant_icon)
props.pennant(im, 568, 6, 52, 64, props.pennant_channel)
im.save('out/bg_v2_test.png')
zoom_save(im, 'out/bg_v2_test_2x.png', 2)
zoom_save(im.crop(0, 20, 320, 130), 'out/bg_v2_topleft_4x.png', 4)
zoom_save(im.crop(320, 20, 320, 130), 'out/bg_v2_topright_4x.png', 4)
print('non-db32', sorted(im.check_db32()))
