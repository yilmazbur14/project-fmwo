import pickle
from pngio import *
rows = pickle.load(open("intro_rows.pkl", "rb"))
small = downsample_nearest(rows, 3, 1, 1)
write_png("painting_640.png", small)
write_png("painting_640_danny_4x.png", scale(crop(small, 250, 30, 400, 150), 4))
write_png("crop_danny_face_2x.png", scale(crop(rows, 860, 110, 1100, 420), 2))
