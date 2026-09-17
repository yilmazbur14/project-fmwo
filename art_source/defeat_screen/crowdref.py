from lib import *
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
c = load(P + 'Assets/Environment/crowd_v2.png')
zoom_save(c.crop(0, 0, 320, 40), 'ref/crowdv2_f0_left_6x.png', 6)
zoom_save(c.crop(320, 0, 320, 40), 'ref/crowdv2_f0_right_6x.png', 6)
zoom_save(c.crop(0, 0, 160, 40), 'ref/crowdv2_f0_a_12x.png', 12)
f = Img(640, 40 * 5 + 8)
for k in range(5):
    f.blit(c.crop(k * 640, 0, 640, 40), 0, k * 42)
zoom_save(f, 'ref/crowdv2_frames_2x.png', 2)
print('ok')
