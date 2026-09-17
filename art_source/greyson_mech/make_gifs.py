import pickle
from pngio import *
from gifio import write_gif
imgs = pickle.load(open('frames.pkl', 'rb'))
BG = (120, 160, 120, 255)
S = 3
ANIMS = [
    ('idle', [(0, 180), (1, 180), (2, 180), (3, 180)]),
    ('laser_charge', [(4, 150), (5, 350)]),
    ('laser_fire', [(6, 250), (7, 250), (8, 250)]),
    ('rocket_volley', [(9, 300), (10, 80), (11, 180)]),
    ('ground_pound', [(12, 280), (13, 200), (14, 80), (15, 450)]),
    ('vulnerable', [(16, 260), (17, 260)]),
    ('hit', [(0, 400), (18, 150)]),          # preview: idle pose then the flinch
    ('defeat', [(19, 140), (20, 160), (21, 220), (22, 2000)]),
]
for name, seq in ANIMS:
    frames = [scale(imgs[i], S, BG) for i, _ in seq]
    n = write_gif(f'gif_{name}.gif', frames, [round(ms / 10) for _, ms in seq])
    print(name, n, 'bytes')
