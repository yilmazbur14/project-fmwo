"""Beast Bixby's full TRANSFORMATION: 26 frames of 320x256, Bixby's feet anchor fixed at (160, 251).
Continues the entrance (Liam/Entrance/bixby_swallow_keys.png frame 2 GULP) and ends exactly on
bixby_beast.png hover frame 0, lifted 40 texels.

  0-2   aftershock of the gulp   (freeze, heartbeat throb, first red glint)
  3-6   cracks ignite            (lava spreads, ears singe, embers, rim catches fire)
  7-9   rising                   (lift-off, shockwave ring, ember swirl, he goes to silhouette)
  10-14 swelling in stages       (bulk, horns one head at a time, collars, tail flame, back bulges)
  15-17 wings burst out          (stubs tear, unfurl, snap open)
  18-19 implosion                (everything sucks inward, near-black hold)
  20    detonation               (white-orange flash burst)
  21-24 reveal                   (smoke clears, eyes ignite one head at a time)
  25    hold                     (= bixby_beast.png frame 0, lifted 40)

Layers: fx_back (rays, ground glow, flash, shockwave) / body / fx_front (rim flames, embers, smoke, glasses)."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pal import PALC, BLACK
import tf_stages as ST
import tf_fx as TFX
import fx2 as FX
import heads as HD

TW, TH, AX, AY = ST.TW, ST.TH, ST.AX, ST.AY
LAYERS = ['fx_back', 'body', 'fx_front']

# per frame: y-lift of the creature, and the suggested duration in ms
LIFT = [0, 0, 0, 0, 0, 0, 0, 5, 13, 21, 26, 30, 34, 36, 38, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40]
MS = [260, 120, 220, 150, 150, 130, 200, 90, 90, 110, 150, 150, 150, 150, 220, 90, 90, 240, 120, 260, 90,
      110, 200, 180, 180, 400]


def blank():
    return ST.blank()


def frame(i):
    back, body, front = blank(), blank(), blank()
    lift = LIFT[i]
    gx, gy = AX, AY - lift

    # ---------------------------------------------------------- 0-6: the dog, cracking open
    if i <= 8:
        eyes = ['shrunk', 'glint', 'ember', 'ember', 'lit', 'lit', 'blaze', 'blaze', 'blaze'][i]
        cracks = [0, 0, 1, 2, 2, 3, 3, 3, 3][i]
        singe = [0, 0, 0, 0, 1, 2, 3, 3, 3][i]
        glow = [0, 1, 1, 1, 2, 2, 3, 3, 3][i]
        squash = 1 if i == 1 else 0
        cv = ST.bixby_stage(eyes=eyes, cracks=cracks, singe=singe, squash=squash, glow=glow)
        shake = 1 if i in (5, 6) else 0
        ST.paste(body, cv, ST.BIX[0] + shake, ST.BIX[1] - lift)
        m = {(x + ST.BIX[0] + shake, y + ST.BIX[1] - lift) for (x, y) in cv.mask()}
        if i >= 1:
            TFX.ground_disc(back, AX, AY - 5, 30 + 3 * i, 4 + 0.5 * i, level=[0, 0.3, 0.35, 0.45, 0.55, 0.7, 0.85, 0.9, 0.8][i])
        if i >= 4:
            TFX.rim_glow(front, m, 'F' if i == 4 else 'O', 'r' if i == 4 else 'Q')
        if i >= 5:
            TFX.rim_flames(front, m, t=i, height=[0, 0, 0, 0, 0, 4, 7, 8, 9][i], seed=3 + i)
        if i >= 2:
            TFX.embers_rising(front, (AX - 46, AY - 120, AX + 46, AY), t=i * 1.4, n=6 + 5 * i, seed=7 + i, speed=7)
        if i >= 7:      # lift-off (the big ground ring itself lives in bixby_transform_shockwave.png)
            r = 26 + (i - 7) * 20
            TFX.ring(back, AX, AY - 4, r, min(8.0, r * 0.26), thick=3 - (i - 7))
            if i == 7:
                TFX.dome(front, AX, AY - 2, 22)
            TFX.ember_swirl(front, AX, AY - 10, t=i, n=16 + 6 * (i - 7), rx=46, ry=26, seed=9)
        if i == 8:
            TFX.rays(back, AX, AY - 46, 10, 30, 108, phase=0.2)
        return dict(fx_back=back, body=body, fx_front=front)

    # ---------------------------------------------------------- 9: the dog goes to silhouette as he rises
    if i == 9:
        cv = ST.bixby_stage(eyes='blaze', cracks=3, singe=3, glow=3)
        m0 = cv.mask()
        m = ST.scale_mask(m0, 1.06, 32, 62)
        m = {(x + ST.BIX[0], y + ST.BIX[1] - lift) for (x, y) in m}
        m = {q for q in m if 0 <= q[0] < TW and 0 <= q[1] < TH}
        TFX.fill_silhouette(body, m)
        TFX.crack_lines(body, m, [(AX - 14, gy - 26, 2.6), (AX + 12, gy - 24, 0.5), (AX, gy - 16, 1.5),
                                  (AX - 20, gy - 40, 2.3), (AX + 18, gy - 42, 0.8)], level=3, seed=23, length=12)
        for (ex, ey) in ((AX - 6, gy - 52), (AX + 6, gy - 52), (AX - 20, gy - 40), (AX + 20, gy - 40)):
            ST.put_eye(body, ex, ey, 'lit', 0.8)
        TFX.rays(back, AX, gy - 40, 12, 34, 130, phase=0.6)
        TFX.ring(back, AX, AY - 4, 74, 8, thick=2)
        TFX.rim_flames(front, m, t=i, height=9, seed=12)
        TFX.ember_swirl(front, AX, gy - 10, t=i, n=26, rx=52, ry=30, seed=11)
        return dict(fx_back=back, body=body, fx_front=front)

    # ---------------------------------------------------------- 10-17: swelling, horns, wings
    if i <= 17:
        spec = {
            10: dict(scale=0.55, horns=(False, False, False), wings=0.0, rays=(14, 40, 150, 0.1)),
            11: dict(scale=0.68, horns=(True, False, False), wings=0.0, rays=(15, 44, 158, 0.5)),
            12: dict(scale=0.78, horns=(True, True, False), wings=0.0, rays=(16, 48, 166, 0.9)),
            13: dict(scale=0.88, horns=(True, True, True), wings=0.0, rays=(17, 52, 172, 1.3)),
            14: dict(scale=0.95, horns=(True, True, True), wings=0.0, rays=(18, 56, 178, 1.7)),
            15: dict(scale=1.0, horns=(True, True, True), wings=0.20, rays=(19, 58, 184, 2.1)),
            16: dict(scale=1.0, horns=(True, True, True), wings=0.58, rays=(20, 60, 190, 2.5)),
            17: dict(scale=1.0, horns=(True, True, True), wings=1.0, rays=(22, 62, 196, 2.9)),
        }[i]
        cv, m, eyes = ST.beast_silhouette(spec['scale'], lift, horns=spec['horns'], wings=spec['wings'],
                                          cracks=3, eyes='lit', seed=21 + i)
        ST.paste(body, cv, 0, 0)
        n, r0, r1, ph = spec['rays']
        TFX.rays(back, AX, gy - 60 * spec['scale'], n, r0, r1, phase=ph)
        TFX.ground_disc(back, AX, AY - 5, 34, 7, level=0.5)
        TFX.rim_flames(front, m, t=i, height=6, seed=5 + i, dense=3)
        TFX.ember_swirl(front, AX, gy - 20, t=i, n=24, rx=58, ry=34, seed=13 + i)
        # new horn / wing beats get an extra ember burst
        if i in (11, 12, 13):
            hx = [AX, AX - 52 * spec['scale'], AX + 52 * spec['scale']][i - 11]
            FX.embers(front, (hx - 20, gy - 96 * spec['scale'], hx + 20, gy - 60 * spec['scale']), 14,
                      seed=41 + i, hot_ratio=0.7, sizes=(1, 2, 3))
        if i == 13:     # the tail flame lights
            tx, ty = ST.scale_pt((13, 124), spec['scale'], 96, 151)
            FX.ember(front, tx + AX - 96, ty + AY - 151 - lift, 3, hot=True)
        if i == 14:     # the back bulges crack open, about to tear
            for bx in (AX - 30, AX + 30):
                TFX.crack_lines(front, m, [(bx, gy - 62, 1.2), (bx, gy - 58, 4.4)], level=3, seed=61 + i, length=7)
        if i >= 15:     # wings tearing out
            FX.embers(front, (AX - 96, gy - 110, AX + 96, gy - 30), 18 + 10 * (i - 15), seed=71 + i,
                      hot_ratio=0.6, sizes=(1, 2, 3))
        if i == 12:     # Liam's glasses fall out of the air and catch on the new left horn
            gxp, gyp = ST.scale_pt((56, 20), spec['scale'], 96, 151)
            HD.glasses_on_horn(front, int(gxp + AX - 96), int(gyp + AY - 151 - lift))
        elif i in (10, 11):
            HD.glasses_on_horn(front, 214 - 6 * i, 40 + 26 * i)
        else:
            gxp, gyp = ST.scale_pt((56, 20), spec['scale'], 96, 151)
            HD.glasses_on_horn(front, int(gxp + AX - 96), int(gyp + AY - 151 - lift))
        return dict(fx_back=back, body=body, fx_front=front)

    # ---------------------------------------------------------- 18-19: implosion
    if i in (18, 19):
        cv, m, eyes = ST.beast_silhouette(1.0, lift, horns=(True, True, True), wings=1.0, cracks=2 if i == 18 else 0,
                                          eyes='ember' if i == 18 else '', seed=31, dark=True)
        ST.paste(body, cv, 0, 0)
        if i == 18:
            TFX.implode_streaks(front, AX, gy - 60, 106, 42, n=26, seed=5)
            TFX.ground_disc(back, AX, AY - 5, 30, 6, level=0.4)
        else:
            # held beat: everything is dark but a white-hot core in the chest
            for (dx, dy, c) in ((0, 0, 'W'), (1, 0, 'L'), (-1, 0, 'L'), (0, 1, 'L'), (0, -1, 'L'),
                                (2, 0, 'O'), (-2, 0, 'O'), (0, 2, 'O'), (0, -2, 'O'), (1, 1, 'O'), (-1, -1, 'O')):
                front.put(AX + dx, gy - 58 + dy, PALC[c])
            TFX.implode_streaks(front, AX, gy - 58, 30, 12, n=14, seed=9, colours=('O', 'o', 'F'))
        return dict(fx_back=back, body=body, fx_front=front)

    # ---------------------------------------------------------- 20: detonation
    if i == 20:
        TFX.flash_disc(back, AX, gy - 62, 102, spikes=20, phase=0.15, sq=0.88)
        cv, m, eyes = ST.beast_silhouette(1.0, lift, horns=(True, True, True), wings=1.0, cracks=0, eyes='',
                                          seed=31, dark=True)
        for (x, y) in m:
            body.put(x, y, BLACK)
        for (ex, ey) in eyes:
            ST.put_eye(body, ex, ey, 'blaze', 1.0)
        FX.embers(front, (AX - 150, gy - 150, AX + 150, gy + 40), 26, seed=83, hot_ratio=0.8, sizes=(2, 3))
        return dict(fx_back=back, body=body, fx_front=front)

    # ---------------------------------------------------------- 21-25: reveal
    eyes_state = {21: 'cold', 22: 'cold', 23: 'mid', 24: 'on', 25: 'on'}[i]
    cv = ST.beast_final(lift=40, eyes=eyes_state)
    ST.paste(body, cv, 0, 0)
    if i == 25:
        return dict(fx_back=back, body=body, fx_front=front)
    m = cv.mask()
    if i == 21:
        TFX.flash_disc(back, AX, gy - 62, 78, spikes=16, phase=0.6, core=0.3, ring_w=0.30, sq=0.88)
        TFX.rim_glow(front, m, 'W', 'L')
        TFX.smoke_ring(front, AX, gy - 40, 100, 44, r=9, n=11, seed=17)
        FX.embers(front, (AX - 140, gy - 140, AX + 140, gy + 30), 30, seed=91, hot_ratio=0.7, sizes=(1, 2, 3))
    elif i == 22:
        TFX.rim_glow(front, m, 'O', 'Q')
        TFX.smoke_ring(front, AX, gy - 36, 116, 52, r=8, n=11, seed=19, holes=0.0)
        FX.embers(front, (AX - 140, gy - 150, AX + 140, gy + 20), 22, seed=93, hot_ratio=0.5, sizes=(1, 2))
    elif i == 23:
        TFX.smoke_ring(front, AX, gy - 30, 124, 56, r=7, n=10, seed=23, holes=0.12)
        FX.embers(front, (AX - 130, gy - 150, AX + 130, gy + 10), 16, seed=95, hot_ratio=0.4, sizes=(1, 2))
        for (ex, ey) in ST.EYES_MID:                      # the middle head's eyes flare as they light
            x, y = ex + ST.BEAST[0], ey + ST.BEAST[1] - 40
            FX.ember(front, x, y, 3, hot=True)
    elif i == 24:
        TFX.smoke_ring(front, AX, gy - 24, 132, 60, r=6, n=9, seed=29, holes=0.15)
        FX.embers(front, (AX - 120, gy - 140, AX + 120, gy), 10, seed=97, hot_ratio=0.3, sizes=(1, 2))
        for (ex, ey) in ST.EYES_L + ST.EYES_R:            # then the side heads
            x, y = ex + ST.BEAST[0], ey + ST.BEAST[1] - 40
            FX.ember(front, x, y, 3, hot=True)
    return dict(fx_back=back, body=body, fx_front=front)


def frames():
    return [frame(i) for i in range(len(MS))]


def flatten(fr):
    c = Canvas(TW, TH)
    for L in LAYERS:
        c.blit(fr[L], 0, 0)
    return c


if __name__ == '__main__':
    import anim_common as AC
    fr = frames()
    cols = 7
    rows = (len(fr) + cols - 1) // cols
    sheet = Canvas(TW * cols, TH * rows)
    for i, f in enumerate(fr):
        sheet.blit(flatten(f), TW * (i % cols), TH * (i // cols))
    AC.preview(sheet, 'tf_contact_1x.png', 1)
    print('ok', len(fr), 'frames')
