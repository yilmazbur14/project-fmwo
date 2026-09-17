"""4-frame aura flicker GIF (preview only - the shipped sprite is static)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from lib import W, H, Canvas
from pngio import write_png, scale, blank, paste
from gifio import write_gif
import render as R, parts as P, aura as AU, poses as PO


def jitter(specs, k, amp=1.3):
    out = []
    for i, (ctrl, w0, w1) in enumerate(specs):
        nc = []
        for j, (x, y) in enumerate(ctrl):
            t = j / max(1, len(ctrl) - 1)
            ph = k * math.pi / 2 + i * 1.1 + j * 0.7
            nc.append((x + math.sin(ph) * amp * t,
                       y - abs(math.cos(ph)) * amp * 0.9 * t))
        out.append((nc, w0 * (1.0 + 0.06 * math.sin(k * 1.6 + i)), w1))
    return out


def frame(k, pose='idle'):
    cv = Canvas()
    if pose == 'idle':
        bm = P.body_mask()
        AU.paint(cv, jitter(AU.IDLE, k), AU.IDLE_SPARKS, bm)
        AU.haze(cv, bm, 5, 0, k)
        R.body(cv)
    else:
        bm = PO.x_body_mask()
        AU.paint(cv, jitter(AU.FLARE, k, 1.8), AU.FLARE_SPARKS, bm)
        AU.haze(cv, bm, 9, 4, k)
        PO.draw_cross(cv)
    return cv.rgba()


SC = 4
frames = []
for k in range(4):
    a = frame(k, 'idle')
    b = frame(k, 'pose')
    strip = blank(W * 2, H, (24, 24, 32, 255))
    paste(strip, a, 0, 0)
    paste(strip, b, W, 0)
    frames.append(scale(strip, SC))
write_gif('preview_aura.gif', frames, [12] * len(frames))
print('preview_aura.gif', W * 2 * SC, H * SC, len(frames), 'frames')
