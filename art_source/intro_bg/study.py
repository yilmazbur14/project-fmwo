from collections import Counter
from pngio import *
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Danny/DannyIntro.png"
w, h, rows = read_png(P)
print(w, h)
c = Counter(px for row in rows for px in row)
print(len(c), "colors")
for px, n in c.most_common(30):
    print("   ", hexc(px), px[3], n)
import pickle
pickle.dump(rows, open("intro_rows.pkl", "wb"))
write_png("crop_danny.png", crop(rows, 770, 100, 1170, 440))
write_png("crop_lbanner.png", crop(rows, 0, 0, 460, 620))
write_png("crop_rbanner.png", crop(rows, 1460, 0, 1920, 620))
write_png("crop_papers.png", scale(crop(rows, 770, 550, 990, 790), 2))
