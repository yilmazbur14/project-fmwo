import sys; sys.dont_write_bytecode = True
import fastball as FB, rig
from view import to_img, zoom, strip
from PIL import Image
names = sys.argv[1:] or [n for n, _ in FB.FRAMES]
poses = dict(FB.FRAMES)
ref = to_img(rig.render({}))
imgs = [zoom(ref, 8)] + [zoom(to_img(FB.render(poses[n])), 8, grid=8) for n in names]
strip(imgs).save('../look.png')
sm = [zoom(ref, 3)] + [zoom(to_img(FB.render(poses[n])), 3) for n in names]
strip(sm).save('../look3.png')
