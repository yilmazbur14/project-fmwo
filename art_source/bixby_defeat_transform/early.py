"""Transformation frames 0-9: normal Bixby after the gulp, cracking open, tearing off the floor and going
to silhouette. There is no beast in them, so the shipped drawings are kept pixel for pixel; only their
colours move onto the redesign's ramps so they lead into the new beast:

  the lava / glow fire    old lemon-orange  ->  the beast's fire ramp (u v P Y)
  the saddle glow and     old wine crimson  ->  the beast's blood-red fur ramp (q r s)
    frame 9's silhouette
  the eyes lighting up    old yellow        ->  the beast's mint (h i j)

Liam's headband keeps the colours of the swallow storyboard that plays right before (a jump there would
be the only thing to see), and normal Bixby keeps bixby.png's palette.
"""
import common as C

SOURCE = C.os.path.join(C.HERE, 'src', 'bixby_transform_before.png')

FIRE = {
    (251, 242, 54, 255): 'P',       # lemon     -> amber
    (255, 247, 160, 255): 'Y',      # pale      -> pale gold
    (245, 138, 56, 255): 'v',       # orange    -> hot ember
    (223, 113, 38, 255): 'u',       # dark orange -> ember
}
CRIMSON = {
    (138, 31, 56, 255): 's',
    (94, 20, 44, 255): 'r',
    (60, 12, 32, 255): 'q',
}
EYES = {
    (255, 247, 160, 255): 'j',
    (251, 242, 54, 255): 'i',
    (245, 138, 56, 255): 'h',
    (223, 113, 38, 255): 'h',
}

# where the old rig stamped the eyes (tf_stages.bixby_eyes / put_eye), in transformation-frame texels
LIFT = [0, 0, 0, 0, 0, 0, 0, 5, 13, 21]
SHAKE = [0, 0, 0, 0, 0, 1, 1, 0, 0, 0]
BIX = (128, 189)


def eye_boxes(i):
    """Inclusive boxes round every eye stamp of frame i (a 1px margin for the stamps' glow corners)."""
    if i == 9:
        gy = 251 - LIFT[9]
        pts = [(160 - 6, gy - 52), (160 + 6, gy - 52), (160 - 20, gy - 40), (160 + 20, gy - 40)]
        return [(x - 1, y - 1, x + 1, y + 1) for (x, y) in pts]
    ox, oy = BIX[0] + SHAKE[i], BIX[1] - LIFT[i]
    boxes = [(ox + 24, oy + 9, ox + 28, oy + 13), (ox + 34, oy + 9, ox + 38, oy + 13)]
    for (sx, sy) in ((10, 22), (16, 22), (45, 21), (53, 21)):
        boxes.append((ox + sx, oy + sy, ox + sx + 2, oy + sy + 3))
    return boxes


def recolour(im, i):
    out = im.copy()
    px = out.load()
    boxes = eye_boxes(i) if i >= 2 else []
    w, h = out.size
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if not c[3]:
                continue
            k = None
            if any(x0 <= x <= x1 and y0 <= y <= y1 for (x0, y0, x1, y1) in boxes):
                k = EYES.get(c)
            if k is None:
                k = FIRE.get(c) or CRIMSON.get(c)
            if k is not None:
                px[x, y] = C.PAL[k]
    return out


def frames():
    old = C.cells(C.load(SOURCE), C.TW, C.TH, 13, 2)
    return [recolour(old[i], i) for i in range(10)]
