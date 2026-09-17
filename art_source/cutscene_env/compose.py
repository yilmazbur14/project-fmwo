"""Compose parallax layers into a 640x360 camera frame (for mockups/checks)."""
from lib import Canvas


def frame(layers, cam_x, cam_w=640, cam_h=360):
    """layers: list of (Canvas, factor, x_offset). Later layers draw on top."""
    out = Canvas(cam_w, cam_h, 'K')
    for (cv, f, off) in layers:
        sx = int(round(cam_x * f)) - off
        for y in range(cam_h):
            row = cv.p[y]
            orow = out.p[y]
            for x in range(cam_w):
                lx = x + sx
                if 0 <= lx < cv.w:
                    k = row[lx]
                    if k is not None:
                        orow[x] = k
    return out
