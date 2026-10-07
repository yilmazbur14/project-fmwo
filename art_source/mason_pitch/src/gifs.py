"""Timed previews of the set on the live Mason arena (a 1920x1080 capture of the fight with Mason and the
player hidden at runtime), at real scale, on the plan's P1 beats. Art preview only: the code's own
extras (the release-to-ball trail, hit flashes, daze stars) are not drawn.

  gif_fastball.gif   READY, wind-up, SET under the strong red badge, RELEASE, flight, the hit on the player
  gif_changeup.gif   READY, the CHANGE_A/B rock, CHANGE_SET under the badge, the lob (own trail, half-rate spin)
  gif_hesitation.gif wind-up, SET under the pale X, PUMP, PUMP_HOLD, the hitch, then the red badge and a fastball
  gif_home_run.gif   a parried fastball batted back: bonk FX, BONK frames, HOME RUN! with the streak pips
  gif_knockdown.gif  the third home run: HOME RUN! (3 pips) and mason_broken's knockdown into the dazed loop
plus a still of a key moment of each (still_*.png).
"""
import json
import math
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.realpath(os.path.join(HERE, '..', 'out'))
GIFS = os.path.join(OUT, 'gifs')
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASSETS = os.path.realpath(PROJ + 'Assets')
os.makedirs(GIFS, exist_ok=True)
FPS = 30
DT = 1.0 / FPS
S = 3
CROP = (360, 140, 1240, 840)            # region of the 1920x1080 screen the previews show
MASON = (960, 280)                      # his body at home
TL = (MASON[0] - 96, MASON[1] - 96)     # his frame's top-left on screen
PLAYER = (495, 753)                     # the player's body (approval mockup spot, down-left of him)
PLAYER_HIT = (495, 745)                 # roughly his hurtbox centre
C = json.load(open(os.path.join(OUT, 'contract.json')))


def guard(p):
    assert not os.path.realpath(p).lower().startswith(ASSETS.lower()), p
    return p


def sheet(path, fw, fh):
    im = Image.open(path).convert('RGBA')
    return [im.crop((i * fw, 0, (i + 1) * fw, fh)).resize((fw * S, fh * S), Image.NEAREST) for i in range(im.width // fw)]


BG = Image.open(os.path.join(HERE, 'cap', 'no_chars.png')).convert('RGBA')
PITCH = sheet(os.path.join(OUT, 'mason_pitch.png'), 64, 64)
BROKEN = sheet(os.path.join(OUT, 'mason_broken.png'), 64, 64)
IDLE = sheet(PROJ + 'Assets/Characters/Mason/mason_sheet.png', 64, 64)
SPIN = sheet(os.path.join(OUT, 'nugget_fastball.png'), 32, 32)
STREAK = sheet(os.path.join(OUT, 'nugget_fastball_streaks.png'), 48, 48)
TRAIL = sheet(os.path.join(OUT, 'nugget_changeup_trail.png'), 48, 48)
BONK = sheet(os.path.join(OUT, 'nugget_bonk.png'), 32, 32)
HR = sheet(os.path.join(OUT, 'home_run.png'), 128, 40)
PIPS = sheet(os.path.join(OUT, 'home_run_pips.png'), 12, 12)
BADGE = sheet(PROJ + 'Assets/Effects/parry_tell_strong.png', 48, 36)
FEINT = sheet(PROJ + 'Assets/Characters/Carter/Demon/demon_feint.png', 24, 24)
PLAYER_IMG = Image.open(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png').convert('RGBA') \
    .crop((0, 32, 32, 64)).resize((96, 96), Image.NEAREST)
BADGE_TIMES = [0.07, 0.07, 0.08, 0.08, 0.07, 0.07]


def tex_to_screen(t):
    return (MASON[0] + (t[0] - 32) * 3, MASON[1] + (t[1] - 32) * 3)


TELL = tex_to_screen(C['mason_pitch']['frames'][3]['tell_side'])
HEAD_HIT = {i: tex_to_screen(e['head_hit']) for i, e in enumerate(C['mason_pitch']['frames'])}
REL = {4: tex_to_screen((10.5, 56.5)), 11: tex_to_screen((11.5, 36.5))}


def direction(v):
    a = math.degrees(math.atan2(v[1], v[0])) % 360
    return int(round(a / 45.0)) % 8


class Scene:
    def __init__(self):
        self.frames = []

    def shot(self, mason, ball=None, overlays=(), player=True):
        c = BG.copy()
        c.alpha_composite(mason, TL)
        if player:
            c.alpha_composite(PLAYER_IMG, (PLAYER[0] - 48, PLAYER[1] - 48))
        if ball:
            centre, spin_i, trail_img = ball
            if trail_img is not None:
                c.alpha_composite(trail_img, (int(centre[0] - 72), int(centre[1] - 72)))
            c.alpha_composite(SPIN[spin_i], (int(centre[0] - 48), int(centre[1] - 48)))
        for img, pos in overlays:
            c.alpha_composite(img, (int(pos[0]), int(pos[1])))
        self.frames.append(c.crop(CROP))

    def save(self, name, still_at=None):
        pal_src = Image.new('RGBA', (self.frames[0].width * 2, self.frames[0].height))
        pal_src.paste(self.frames[0], (0, 0))
        pal_src.paste(self.frames[len(self.frames) // 2], (self.frames[0].width, 0))
        pal = pal_src.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        q = [f.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE) for f in self.frames]
        q[0].save(guard(os.path.join(GIFS, name + '.gif')), save_all=True, append_images=q[1:],
                  duration=int(round(DT * 1000)), loop=0, disposal=1)
        if still_at is not None:
            self.frames[still_at].save(guard(os.path.join(GIFS, 'still_' + name.replace('gif_', '') + '.png')))
        return len(self.frames)


def badge(t):
    """the strong badge's looping frame at time t since it went up, positioned by its bottom tip"""
    loop = sum(BADGE_TIMES)
    u = t % loop
    i = 0
    acc = 0.0
    for k, ft in enumerate(BADGE_TIMES):
        acc += ft
        if u < acc:
            i = k
            break
    return (BADGE[i], (TELL[0] - 72, TELL[1] - 108))


def feint(t):
    i = 0 if t < 0.05 else (1 if t < 0.09 else 2)
    return (FEINT[i], (TELL[0] - 36, TELL[1] - 72))


def hold(sc, frame, secs, **kw):
    for _ in range(int(round(secs * FPS))):
        sc.shot(frame, **kw)


def windup_fastball(sc):
    hold(sc, PITCH[0], 0.60)
    hold(sc, PITCH[1], 0.25)
    hold(sc, PITCH[2], 0.30)


def fly(a, b, t, arc=0.0):
    x = a[0] + (b[0] - a[0]) * t
    y = a[1] + (b[1] - a[1]) * t - arc * 4 * t * (1 - t)
    return (x, y)


def pitch_fastball(sc, badge_on=True, result='hit', t0_overlays=None):
    """t = 0 at the SET. Release +0.30, contact +0.42. result: 'hit' or 'parry' (returns the contact frame index)"""
    t = 0.0
    a, b = REL[4], PLAYER_HIT
    dirn = direction((b[0] - a[0], b[1] - a[1]))
    contact_idx = None
    while t < 0.42 + 0.35 - 1e-6:
        ov = []
        if badge_on and t < 0.52:
            ov.append(badge(t))
        if t < 0.30:
            fr = PITCH[3]
        elif t < 0.36:
            fr = PITCH[4]
        else:
            fr = PITCH[5]
        ball = None
        if 0.30 <= t < 0.42:
            u = (t - 0.30) / 0.12
            p = fly(a, b, u)
            ball = (p, int(t / 0.05) % 4, STREAK[dirn * 2 + int(t / 0.06) % 2])
        if t >= 0.42 and result == 'hit' and t < 0.42 + 0.30:
            k = min(4, int((t - 0.42) / 0.06))
            ov.append((BONK[k] if k > 0 else BONK[1], (b[0] - 48, b[1] - 48)))
        if result == 'parry' and t >= 0.42:
            if contact_idx is None:
                contact_idx = len(sc.frames)
            break
        sc.shot(fr, ball=ball, overlays=ov)
        t += DT
    return contact_idx


def home_run(sc, pips_filled, then='bonk'):
    """the ball batted back from the player to his head in 0.16 s, then the bonk"""
    a = PLAYER_HIT
    b = HEAD_HIT[5]
    dirn = direction((b[0] - a[0], b[1] - a[1]))
    t = 0.0
    while t < 0.16 - 1e-6:
        p = fly(a, b, t / 0.16)
        sc.shot(PITCH[5], ball=(p, int(t / 0.05) % 4, STREAK[dirn * 2 + int(t / 0.06) % 2]))
        t += DT
    # arrival
    word_bottom = (MASON[0], TL[1] + 192 + 18 + 120)
    t = 0.0
    total = 1.2 if then == 'bonk' else 3.4
    hr_times = [0.05, 0.06, 0.06, 0.30, 0.06, 0.06]
    while t < total:
        ov = []
        k = int(t / 0.06)
        if k < 5:
            ov.append((BONK[k], (b[0] - 48, b[1] - 48)))
        # HOME RUN!: steps 0-5 once, then holds on 3 until 0.9 s, then glints again
        acc, hi = 0.0, 3
        for i, ft in enumerate(hr_times):
            acc += ft
            if t < acc:
                hi = i
                break
        if t < 0.9 or then != 'bonk':
            if t < 2.6:
                ov.append((HR[hi], (word_bottom[0] - 192, word_bottom[1] - 120)))
                for j in range(3):
                    pip = PIPS[1 if j < pips_filled else 0]
                    ov.append((pip, (word_bottom[0] - 54 + j * 36, word_bottom[1] + 4)))
        if then == 'bonk':
            fr = PITCH[12] if t < 0.12 else PITCH[13] if t < 0.27 else PITCH[14] if t < 0.45 else IDLE[0]
        else:
            bt = [0.10, 0.12, 0.14, 0.12]
            if t < sum(bt):
                acc, fi = 0.0, 0
                for i, ft in enumerate(bt):
                    acc += ft
                    if t < acc:
                        fi = i
                        break
                fr = BROKEN[fi]
            else:
                fr = BROKEN[4 + int((t - sum(bt)) / 0.35) % 2]
        sc.shot(fr, overlays=ov)
        t += DT


def make_fastball():
    sc = Scene()
    windup_fastball(sc)
    n0 = len(sc.frames)
    pitch_fastball(sc)
    hold(sc, IDLE[0], 0.4)
    return sc.save('gif_fastball', still_at=n0 + 3)


def make_changeup():
    sc = Scene()
    hold(sc, PITCH[0], 0.60)
    for k in range(4):
        hold(sc, PITCH[8 + (k % 2)], 0.20)
    a, b = REL[11], PLAYER_HIT
    dirn = direction((b[0] - a[0], b[1] - a[1]))
    t = 0.0
    n0 = len(sc.frames)
    while t < 0.64 + 0.35:
        ov = []
        if t < 0.74:
            ov.append(badge(t))
        fr = PITCH[10] if t < 0.30 else PITCH[11]
        ball = None
        if 0.30 <= t < 0.64:
            u = (t - 0.30) / 0.34
            p = fly(a, b, u, arc=70)
            ball = (p, int(t / 0.10) % 4, TRAIL[dirn * 2 + int(t / 0.11) % 2])
        if t >= 0.64 and t < 0.94:
            k = min(4, int((t - 0.64) / 0.06))
            ov.append((BONK[max(1, k)], (b[0] - 48, b[1] - 48)))
        sc.shot(fr, ball=ball, overlays=ov)
        t += DT
    hold(sc, IDLE[0], 0.4)
    return sc.save('gif_changeup', still_at=n0 + 14)


def make_hesitation():
    sc = Scene()
    windup_fastball(sc)
    t = 0.0
    n0 = len(sc.frames)
    while t < 0.50:
        ov = [feint(t)]
        fr = PITCH[3] if t < 0.30 else PITCH[6] if t < 0.40 else PITCH[7]
        sc.shot(fr, overlays=ov)
        t += DT
    hold(sc, PITCH[3], 0.15)            # the hitch back to the set
    pitch_fastball(sc)                  # then the red badge and a real fastball
    hold(sc, IDLE[0], 0.4)
    return sc.save('gif_hesitation', still_at=n0 + 4)


def make_home_run():
    sc = Scene()
    hold(sc, PITCH[3], 0.10, overlays=[badge(0.0)])
    pitch_fastball(sc, result='parry')
    n0 = len(sc.frames)
    home_run(sc, pips_filled=1, then='bonk')
    hold(sc, IDLE[0], 0.3)
    return sc.save('gif_home_run', still_at=n0 + 8)


def make_knockdown():
    sc = Scene()
    hold(sc, PITCH[3], 0.10, overlays=[badge(0.0)])
    pitch_fastball(sc, result='parry')
    n0 = len(sc.frames)
    home_run(sc, pips_filled=3, then='broken')
    return sc.save('gif_knockdown', still_at=n0 + 22)


if __name__ == '__main__':
    for fn in (make_fastball, make_changeup, make_hesitation, make_home_run, make_knockdown):
        print(fn.__name__, fn(), 'frames')
