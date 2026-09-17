from whirl import *
from gifio import write_gif
from pngio import scale
imgs = [whirl_frame(i).rgba() for i in range(13, 21)]
d = [8, 14, 11, 11, 11, 11, 11, 10]
frames = [[[p[:3] for p in row] for row in scale(rgba_on(im), 2)] for im in imgs]
write_gif('../w_proto.gif', frames * 2, d * 2)
print('ok')
