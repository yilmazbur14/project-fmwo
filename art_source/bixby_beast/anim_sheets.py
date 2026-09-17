"""Frame lists (layered) for every beast Bixby combat sheet. Each frame is a dict of 192x160 canvases:
fx_back (floor / behind), wings, body, fx_front. Layer order bottom -> top is LAYERS."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
import anim_rig as AR
import beast_poses as BP
import beast_fx as BF

LAYERS = ['fx_back', 'wings', 'body', 'fx_front']


def frame(P, dy, fx):
    wings, body = AR.render(P, dy=dy)
    back, front = fx
    return dict(fx_back=back, wings=wings, body=body, fx_front=front)


def fly():
    out = []
    for i in range(3):
        P, d = BP.fly_pose(i)
        out.append(frame(P, d + BP.DY + 2, BF.fly_fx(i)))
    return out


def land():
    return [frame(BP.land_pose(i), BP.DY, BF.land_fx(i)) for i in range(3)]


def recover():
    out = []
    for i in range(4):
        P = BP.recover_pose(i)
        out.append(frame(P, BP.DY, BF.recover_fx(i, P)))
    return out


def hit():
    out = []
    for i in range(2):
        P = BP.hit_pose(i)
        out.append(frame(P, BP.DY, BF.hit_fx(i, P)))
    return out


def takeoff():
    return [frame(BP.takeoff_pose(i), BP.DY, BF.takeoff_fx(i)) for i in range(3)]


def roar():
    out = []
    for i in range(3):
        P = BP.roar_pose(i)
        out.append(frame(P, BP.DY, BF.roar_fx(i, P)))
    return out


SHEETS = dict(fly=fly, land=land, recover=recover, hit=hit, takeoff=takeoff, roar=roar)


def flatten(fr, w=192, h=160):
    out = Canvas(w, h)
    for L in LAYERS:
        if fr.get(L) is not None:
            out.blit(fr[L], 0, 0)
    return out


if __name__ == '__main__':
    import anim_common as AC
    tag = sys.argv[1]
    names = sys.argv[2:] or list(SHEETS)
    rows = []
    for n in names:
        frs = SHEETS[n]()
        rows.append(AC.strip_of([flatten(f) for f in frs]))
    Wd = max(r.w for r in rows)
    sheet = Canvas(Wd, 160 * len(rows))
    for j, r in enumerate(rows):
        sheet.blit(r, 0, 160 * j)
    scale_ = 2 if len(names) > 1 else 3
    AC.preview(sheet, tag + '.png', scale_, guides=False)
    print('ok')
