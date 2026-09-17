"""render frames in subprocesses (retry on crash), return {i: rgba}"""
import os
import sys
import pickle
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(HERE), 'v2cache')
os.makedirs(CACHE, exist_ok=True)


def render(idx, retries=3, use_cache=False):
    imgs = {}
    for i in idx:
        path = os.path.join(CACHE, 'f%02d.pkl' % i)
        if use_cache and os.path.exists(path):
            imgs[i] = pickle.load(open(path, 'rb'))
            continue
        for attempt in range(retries):
            r = subprocess.run([sys.executable, os.path.join(HERE, 'render_frame.py'), str(i), path],
                               cwd=HERE, capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(path):
                break
            print('frame %d attempt %d failed (%d): %s' % (i, attempt, r.returncode, (r.stderr or '')[-800:]))
        imgs[i] = pickle.load(open(path, 'rb'))
    return imgs


if __name__ == '__main__':
    from base2 import strip, blank, paste, rgba_on, write_png, scale
    idx = [int(a) for a in sys.argv[1].split(',')]
    s = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    imgs = render(idx)
    strip([imgs[i] for i in idx], s, sys.argv[2])
