"""Animated previews at the proposed timings, cropped from the game-scale mocks and shown at 2x
(nearest) so the texels are visible. Nothing here writes into the project."""
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image
import ev2_mocklib as M
import ev2_mock as E
import break_gauge as BG
import mash_meter as MM
import tier_stamps as TS
import dodge_tell as DT
from ev2_common import Canvas

OUT = E.OUT
Z = 2


def gif(frames, name):
    ims = [f[0].convert('RGB').resize((f[0].width * Z, f[0].height * Z), Image.NEAREST) for f in frames]
    durs = [max(20, int(round(f[1] / 10.0)) * 10) for f in frames]
    p = os.path.join(OUT, name)
    ims[0].save(p, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1)
    print('wrote', os.path.abspath(p), len(ims), 'frames', sum(durs), 'ms')


def top_hud(gauge_items, word=None):
    w = E.base(21, lambda l: M.player4(l, 10, (1000, 700)))
    w = E.finish(w, gauge_items + ([word] if word else []))
    return w.crop((700, 30, 1220, 200))


def gauge_anim():
    fr = []
    for pct in (0.0, 0.15, 0.3, 0.45, 0.6, 0.75):
        fr.append((top_hud([E.gauge_img(pct)]), 350))
    for loop in range(3):
        for k in range(4):
            fr.append((top_hud([E.gauge_img(0.88, pulse=k)]), BG.PULSE_MS[k]))
    word_frames = [M.canvas_img(f, 3) for f in E.G['break_text']]
    wpos = (E.GAUGE_AT[0] + (384 - word_frames[0].width) / 2.0, E.GAUGE_AT[1] + 21 + 6)
    t = 0
    for k in range(6):
        fr.append((top_hud([E.shatter_img(k)], (word_frames[(t // 80) % 2], wpos)), BG.SHATTER_MS[k]))
        t += BG.SHATTER_MS[k]
    while t < 1000:
        fr.append((top_hud([E.gauge_img(0.0, locked=True)], (word_frames[(t // 80) % 2], wpos)), 80))
        t += 80
    fr.append((top_hud([E.gauge_img(0.0, locked=True)]), 800))
    gif(fr, 'anim_break_gauge.gif')


def prompt_crop(meter, text):
    hud = Image.new('RGBA', (560, 230), (117, 156, 84, 255))
    feet = (280, 0)
    E.prompt(hud, feet, meter, text, lit_side='right', pressed_side='left')
    return hud


def mash_anim():
    A = MM.build()
    T = TS.build()
    mash = [E.mash_text(0), E.mash_text(1)]
    fr = []
    banked = []
    value = 0.0
    for bar in range(3):
        # filling: a few steps up to the bar
        for s in range(1, 5):
            value = bar + s * 0.22
            fr.append((prompt_crop(MM.composite(value, banked=banked, glint_frame=3), mash[s % 2]), 90))
        # the bank flash
        for k in range(4):
            meter = MM.composite(bar + 1.0, banked=banked, flash=(bar, k))
            fr.append((prompt_crop(meter, M.canvas_img(T['qte_tier_%d' % (bar + 1)][k % 2], 3)), MM.FLASH_MS[k]))
        banked.append(bar)
        # the stamp holds while the glint sweeps
        for k in range(4):
            meter = MM.composite(bar + 1.0, banked=banked, glint_frame=k)
            fr.append((prompt_crop(meter, M.canvas_img(T['qte_tier_%d' % (bar + 1)][k % 2], 3)), MM.BANKED_MS[k]))
    for k in range(6):
        full = A['qte_meter3_full'][k % 2]
        fr.append((prompt_crop(full, M.canvas_img(T['qte_tier_3'][k % 2], 3)), 80))
    gif(fr, 'anim_mash_meter.gif')


def tells_anim():
    def scene(frame_red, frame_yel):
        w = E.base(21)
        left = w.copy()
        E.place_tell(left, (128, 104), frame_red, red=True)
        right = w.copy()
        E.place_tell(right, (128, 104), frame_yel)
        box = (780, 190, 1140, 420)
        out = Image.new('RGBA', (2 * (box[2] - box[0]) + 10, box[3] - box[1]), (16, 14, 26, 255))
        out.alpha_composite(left.crop(box), (0, 0))
        out.alpha_composite(right.crop(box), (box[2] - box[0] + 10, 0))
        return out
    fr = []
    red_ms = [90, 90, 110, 110, 90, 90]
    t = 0
    seq = []
    # the yellow one: ignite, peak once, then the loop; the red one loops from frame 0
    ytimes = DT.DURATIONS_MS
    for step in range(0, 1400, 10):
        # red frame at time step
        rt = step % sum(red_ms)
        acc, rf = 0, 0
        for i, d in enumerate(red_ms):
            if rt < acc + d:
                rf = i
                break
            acc += d
        if step < ytimes[0]:
            yf = 0
        elif step < ytimes[0] + ytimes[1]:
            yf = 1
        else:
            lt = (step - ytimes[0] - ytimes[1]) % sum(ytimes[2:])
            acc, yf = 0, 2
            for i, d in enumerate(ytimes[2:]):
                if lt < acc + d:
                    yf = 2 + i
                    break
                acc += d
        seq.append((rf, yf))
    # collapse runs
    run = []
    for s in seq:
        if run and run[-1][0] == s:
            run[-1][1] += 10
        else:
            run.append([s, 10])
    for (rf, yf), d in run:
        fr.append((scene(rf, yf), d))
    gif(fr, 'anim_tells.gif')


if __name__ == '__main__':
    gauge_anim()
    mash_anim()
    tells_anim()
