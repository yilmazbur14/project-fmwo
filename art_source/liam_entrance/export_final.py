"""Write the final PNG strips to Assets/Characters/Liam/Entrance/ (horizontal strips, frame 0 leftmost) plus
per-frame PNGs in scratchpad/le_frames/ for building the .aseprite files, then lint every strip."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Canvas
from pngio import read_png
import throne
import carriers
import liam_seated
import slap
import swallow
import transform

DEST = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Liam/Entrance'
HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.normpath(os.path.join(HERE, '..', 'le_frames'))
os.makedirs(DEST, exist_ok=True)
os.makedirs(FRAMES, exist_ok=True)


def strip(frames):
    w, h = frames[0].w, frames[0].h
    out = Canvas(w * len(frames), h)
    for i, f in enumerate(frames):
        assert (f.w, f.h) == (w, h)
        out.blit(f, i * w, 0)
    return out


def lint(path):
    w, h, px = read_png(path)
    alphas, cols = set(), set()
    for row in px:
        for p in row:
            alphas.add(p[3])
            if p[3]:
                cols.add(tuple(p[:3]))
    ok = alphas <= {0, 255}
    return '%s %dx%d colours=%d alphas=%s %s' % (os.path.basename(path), w, h, len(cols), sorted(alphas), 'OK' if ok else 'BAD ALPHA')


def main():
    f0, f1 = throne.build()
    walk = carriers.c1_walk()
    keys, fed = slap.build()
    sets = {
        'liam_throne': [f0, f1],
        'liam_carriers': carriers.build_all(),
        'liam_carrier_walk': walk,
        'liam_throne_seated': [liam_seated.build()],
        'liam_slap_keys': keys,
        'bixby_fedup': [fed],
        'bixby_swallow_keys': swallow.build(),
        'bixby_transform_keys': transform.build(),
    }
    for name, frames in sets.items():
        path = os.path.join(DEST, name + '.png')
        strip(frames).save(path)
        for i, f in enumerate(frames):
            f.save(os.path.join(FRAMES, '%s_f%d.png' % (name, i)))
        print(lint(path), '| frames', len(frames), 'x', '%dx%d' % (frames[0].w, frames[0].h))


if __name__ == '__main__':
    main()
