"""Render body sheets for review (scratch look/ only): python kjr_preview.py [sheet ...]"""
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kjr as R  # noqa: E402
import kjr_render as RR  # noqa: E402
import kjr_poses as PZ  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def render_sheet(name, frames):
    out = []
    for pose, opt in frames:
        kw = dict(opt)
        if kw.pop('jaw_from_pose', False):
            kw['jaw'] = pose.get('jaw', (0.0,))[0]
        px, fx, info = RR.render_body(pose, **kw)
        out.append((px, fx, info))
    return out


def strip(name, rendered, s=2, mark=True):
    ims = []
    for px, fx, info in rendered:
        im = K.up(K.render(px, R.FW, R.FH), s, K.MAT)
        if mark:
            d = ImageDraw.Draw(im)
            for key, col in (('FEET', (255, 255, 0)), ('RIDER_SEAT', (255, 140, 0)), ('FOOT_IMPACT', (255, 0, 0)),
                             ('MOUTH', (0, 255, 255)), ('NECK', (255, 0, 255))):
                p = info.get(key)
                if p:
                    x, y = p[0] * s + s // 2, p[1] * s + s // 2
                    d.line((x - 4, y, x + 4, y), fill=col)
                    d.line((x, y - 4, x, y + 4), fill=col)
        ims.append(im)
    w = sum(i.width for i in ims) + 4 * (len(ims) - 1)
    row = Image.new('RGBA', (w, ims[0].height + 16), (20, 20, 24, 255))
    ImageDraw.Draw(row).text((4, 2), name, fill=(255, 255, 255))
    x = 0
    for i in ims:
        row.paste(i, (x, 16))
        x += i.width + 4
    return row


if __name__ == '__main__':
    want = sys.argv[1:]
    for name, frames in PZ.sheets().items():
        if want and name not in want:
            continue
        t = time.time()
        rd = render_sheet(name, frames)
        for i, (px, fx, info) in enumerate(rd):
            st = K.stats(K.render(px, R.FW, R.FH))
            a = K.audit(px, fx)
            xs = [x for (x, y) in px]
            ys = [y for (x, y) in px]
            print('%s f%d black %.1f%% cols %d bbox %s audit %s' % (name, i, 100 * st['black'], st['colours'],
                  (min(xs), min(ys), max(xs), max(ys)), {k: len(v) for k, v in a.items() if v}))
        strip(name, rd).save(os.path.join(K.LOOK, 'pv_%s.png' % name))
        print(name, 'took %.1fs' % (time.time() - t))
