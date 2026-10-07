"""The mocks: the whole ending on the god fight's real void, drawn the way the game draws it (scene.py's numbers,
checked against a real capture), from the EXPORTED sheets in the approval folder. 960x540 = the 1920x1080 view at half,
like the project's captures. python mock.py [side|back] [a|b] [success|fail]  (no args: everything)"""
import math
import sys
import numpy as np
from PIL import Image
from common import *
import scene
import energy as E
from scene import GOD_POINT, VIEW_ZOOM, VIEW_FOCUS

TAKES = {"a": "take_a_blue", "b": "take_b_hype"}
FPS = 15
DT = 1.0 / FPS
CORE = (958.5, 283.5)   # his visible chest core: texel (159.5, 117.5) of his frame

# Each staging: where he stands (MainPlayer origin; his 48 cells centred on it), the ball's and the beam's points in
# his cell, the beam's angle (screen, y down), and the shout's anchor off his origin.
STAGES = {
    "side": dict(origin=(266.0, 975.0), ball=(14.5, 29.0), muzzle=(36.5, 12.5), angle=-math.pi / 4,
                 shout=(40.0, -105.0), ken=(400.0, 80.0), release_view=(0.75, (630.0, 612.0)), dissolve_view=(0.86, (820.0, 470.0))),
    "back": dict(origin=(960.0, 1290.0), ball=(33.0, 28.0), muzzle=(23.5, 11.5), angle=-math.pi / 2,
                 shout=(-250.0, -60.0), ken=(-360.0, -20.0), release_view=(0.70, (960.0, 800.0)), dissolve_view=(0.78, (960.0, 730.0))),
}
BAR_ZOOM = [0.9, 1.2, 1.6, 2.1, 2.8]
BAR_FOCUS = [0.35, 0.55, 0.72, 0.86, 1.0]
SHOUT_SCALE = [4.0, 4.5, 5.0, 5.5, 7.0]   # screen px a texel at 1920x1080


def cells(img, w, h):
    return [[img.crop((i * w, j * h, i * w + w, j * h + h)) for i in range(img.width // w)]
            for j in range(img.height // h)]


class Art:
    def __init__(self, take):
        d = APPROVAL + "/" + TAKES[take] + "/"
        L = lambda n: Image.open(d + n).convert("RGBA")
        P = lambda n: Image.open(APPROVAL + "/player/" + n).convert("RGBA")
        self.burak = {"side": cells(P("player_final_beam_side.png"), 48, 48)[0], "back": cells(P("player_final_beam_back.png"), 48, 48)[0]}
        self.aura = {st: cells(L("final_beam_aura_%s.png" % st), 64, 64) for st in ("side", "back")}
        self.ball = cells(L("final_beam_ball.png"), 64, 64)
        self.ball_glow = cells(L("final_beam_ball_glow.png"), 64, 64)
        self.fizzle = cells(L("final_beam_ball_fizzle.png"), 64, 64)[0]
        self.fizzle_glow = cells(L("final_beam_ball_fizzle_glow.png"), 64, 64)[0]
        self.muzzle = cells(L("final_beam_muzzle.png"), 80, 80)[0]
        self.muzzle_glow = cells(L("final_beam_muzzle_glow.png"), 80, 80)[0]
        self.start = cells(L("final_beam_start.png"), 64, E.BODY_H)[0]
        self.start_glow = cells(L("final_beam_start_glow.png"), 64, E.BODY_GLOW_H)[0]
        self.body = cells(L("final_beam_body.png"), 32, E.BODY_H)[0]
        self.body_glow = cells(L("final_beam_body_glow.png"), 32, E.BODY_GLOW_H)[0]
        self.spiral = cells(L("final_beam_spiral.png"), 32, E.BODY_H)[0]
        self.head = cells(L("final_beam_head.png"), E.HEAD, E.HEAD)[0]
        self.head_glow = cells(L("final_beam_head_glow.png"), E.HEAD, E.HEAD)[0]
        self.impact = cells(L("final_beam_impact.png"), E.IMPACT, E.IMPACT)[0]
        self.impact_glow = cells(L("final_beam_impact_glow.png"), E.IMPACT, E.IMPACT)[0]
        self.words = cells(L("beam_shout_words.png"), 96, 16)[0]
        self.dis = cells(L("god_disintegrate.png"), 320, 224)[0]
        self.dis_glow = cells(L("god_disintegrate_glow.png"), 320, 224)[0]
        self.dis_ash = {st: cells(L("god_disintegrate_ash_%s.png" % st), 480, 352)[0] for st in ("side", "back")}
        self.ref = cells(L("god_reform.png"), 320, 224)[0]
        self.ref_glow = cells(L("god_reform_glow.png"), 320, 224)[0]
        self.ref_ash = {st: cells(L("god_reform_ash_%s.png" % st), 480, 352)[0] for st in ("side", "back")}


def cell_to_world(origin, pt):
    return (origin[0] + 3.0 * (pt[0] - 24.0), origin[1] + 3.0 * (pt[1] - 24.0))


def ease_out_back(x):
    c1, c3 = 1.70158, 2.70158
    x = min(max(x, 0.0), 1.0)
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def word_trim(img):
    bb = img.getbbox()
    return img.crop(bb) if bb else img


def draw_word(cv, img, screen_xy, px, alpha=1.0):
    """Centred on screen_xy (in the 960 render), px screen px a texel at 1080p."""
    im = word_trim(img)
    k = px * cv.rs
    w, h = im.width * k, im.height * k
    x = min(max(screen_xy[0] - w / 2, 8), cv.w - w - 8)
    y = min(max(screen_xy[1] - h / 2, 8), cv.h - h - 8)
    cv._draw(im, np.array([[k, 0], [0, k]], np.float32), np.array([x, y], np.float32), "normal", alpha)


def draw_mash_ui(cv, bars, flash_red=False, label=True):
    """A stand-in for the mash meter (the real one is the game's): five pips, bottom centre."""
    pw, ph, gap = 34, 12, 6
    total = 5 * pw + 4 * gap
    x0, y0 = cv.w / 2 - total / 2, cv.h - 40
    cv.rect_screen(x0 - 5, y0 - 5, total + 10, ph + 10, (0, 0, 0), 0.75)
    for i in range(5):
        lit = i < bars
        col = (230, 60, 60) if flash_red else ((251, 242, 54) if lit else (60, 52, 80))
        cv.rect_screen(x0 + i * (pw + gap), y0, pw, ph, col, 1.0)
        if lit and not flash_red:
            cv.rect_screen(x0 + i * (pw + gap), y0, pw, 3, (255, 255, 255), 0.9)


def draw_god_bar(cv, fill, alpha=1.0, flash=0.0):
    """A stand-in for his boss bar's fill, to show the +5 coming back on a fail."""
    x0, y0, w, h = 362, 54, 236, 10
    cv.rect_screen(x0 - 3, y0 - 3, w + 6, h + 6, (10, 8, 20), 0.85 * alpha)
    cv.rect_screen(x0, y0, w * fill, h, (36, 100, 220), alpha)
    if flash:
        cv.rect_screen(x0, y0, w * fill, h, (255, 255, 255), flash * alpha)


class Shot:
    """One frame's state."""

    def __init__(self):
        self.zoom, self.focus = VIEW_ZOOM, VIEW_FOCUS
        self.shake = (0.0, 0.0)
        self.god = ("hover", 0)
        self.god_alpha = 1.0
        self.runes_alpha = 1.0
        self.burak = 0
        self.aura = None          # (level, frame)
        self.ball = None          # (size 0-4, frame)
        self.fizzle = None
        self.beam = None          # dict(len, thick, frame, alpha, muzzle)
        self.impact = None
        self.word = None          # (index, scale_px, pop)
        self.bars = None
        self.bars_red = False
        self.flash = 0.0
        self.flash_col = (255, 255, 255)
        self.god_bar = None
        self.t = 0.0


def render(art, stage, take, s):
    st = STAGES[stage]
    cv = Canvas()
    cv.set_camera(s.zoom, (s.focus[0] + s.shake[0], s.focus[1] + s.shake[1]))
    scene.draw_void(cv)
    if s.runes_alpha > 0:
        scene.draw_runes(cv, s.t, s.runes_alpha)
    kind, i = s.god
    if kind == "hover":
        scene.draw_god(cv, scene.god_hover(i), scene.god_aura(i), alpha=s.god_alpha)
    elif kind == "hit":
        scene.draw_god(cv, scene.god_hit(i), scene.god_hit_aura(i), alpha=s.god_alpha)
    elif kind in ("dis", "ref"):
        body = art.dis if kind == "dis" else art.ref
        glow = art.dis_glow if kind == "dis" else art.ref_glow
        ash = (art.dis_ash if kind == "dis" else art.ref_ash)[stage]
        cv.sprite(body[i], (160, 223), GOD_POINT, 3.0)
        cv.sprite(glow[i], (160, 223), GOD_POINT, 3.0, mode="add")
        cv.sprite(ash[i], (200, 335), GOD_POINT, 3.0)
    origin = st["origin"]
    if s.aura is not None:
        lv, f = s.aura
        cv.sprite(art.aura[stage][lv][f], (32, 32), origin, 3.0, mode="add")
    cv.sprite(art.burak[stage][s.burak], (24, 24), origin, 3.0)
    if s.ball is not None:
        size, f = s.ball
        p = cell_to_world(origin, st["ball"])
        cv.sprite(art.ball_glow[size][f], (32, 32), p, 3.0, mode="add")
        cv.sprite(art.ball[size][f], (32, 32), p, 3.0)
    if s.fizzle is not None:
        p = cell_to_world(origin, st["ball"] if s.beam is None and s.burak < 5 else st["muzzle"])
        cv.sprite(art.fizzle_glow[s.fizzle], (32, 32), p, 3.0, mode="add")
        cv.sprite(art.fizzle[s.fizzle], (32, 32), p, 3.0)
    if s.beam is not None:
        draw_beam(cv, art, stage, s.beam)
    if s.impact is not None:
        IC = (E.IMPACT / 2, E.IMPACT / 2)
        cv.sprite(art.impact_glow[s.impact], IC, CORE, 3.0, mode="add")
        cv.sprite(art.impact[s.impact], IC, CORE, 3.0)
    if s.flash > 0:
        cv.flash(s.flash_col, s.flash)
    if s.god_bar is not None:
        draw_god_bar(cv, *s.god_bar)
    if s.bars is not None:
        draw_mash_ui(cv, s.bars, s.bars_red)
    if s.word is not None:
        idx, px, pop = s.word[:3]
        released = len(s.word) > 3 and s.word[3]
        off = st["ken"] if released else st["shout"]
        anchor = cv.world_to_screen((origin[0] + off[0], origin[1] + off[1]))
        draw_word(cv, art.words[idx], anchor, px * (1 + 0.35 * pop))
    return cv.image()


def draw_beam(cv, art, stage, b):
    st = STAGES[stage]
    a = st["angle"]
    d = (math.cos(a), math.sin(a))
    hand = cell_to_world(st["origin"], st["muzzle"])
    L = b["len"] / 3.0   # texels
    f = b["frame"] % 4
    th = b.get("thick", 1.0)
    al = b.get("alpha", 1.0)
    at = lambda u: (hand[0] + d[0] * 3.0 * u, hand[1] + d[1] * 3.0 * u)
    if L > 0:
        # body tiles stop under the head's sphere (30 texels short of the tip)
        n = max(0, int(math.ceil((L - 30 - 64) / 32.0))) if b.get("head", True) else max(0, int(math.ceil((L - 64) / 32.0)))
        # while it is shorter than the start piece, only as much of the start as it has travelled
        cut = max(1, min(64, int(math.ceil(L))))
        sg = art.start_glow[f].crop((0, 0, cut, E.BODY_GLOW_H))
        sb = art.start[f].crop((0, 0, cut, E.BODY_H))
        if L >= 64:
            cv.sprite(sg, (0, E.BODY_GLOW_H / 2), hand, 3.0, rot=a, mode="add", alpha=al, sy=th)
        for k in range(n):
            cv.sprite(art.body_glow[f], (0, E.BODY_GLOW_H / 2), at(64 + 32 * k), 3.0, rot=a, mode="add", alpha=al, sy=th)
        cv.sprite(sb, (0, E.BODY_H / 2), hand, 3.0, rot=a, alpha=al, sy=th)
        for k in range(n):
            cv.sprite(art.body[f], (0, E.BODY_H / 2), at(64 + 32 * k), 3.0, rot=a, alpha=al, sy=th)
            cv.sprite(art.spiral[f], (0, E.BODY_H / 2), at(64 + 32 * k), 3.0, rot=a, mode="add", alpha=al, sy=th)
        if b.get("head", True):
            tip = at(L)
            cv.sprite(art.head_glow[f], (78, E.HEAD / 2), tip, 3.0, rot=a, mode="add", alpha=al, sx=th, sy=th)
            cv.sprite(art.head[f], (78, E.HEAD / 2), tip, 3.0, rot=a, alpha=al, sx=th, sy=th)
    m = b.get("muzzle")
    if m is not None:
        cv.sprite(art.muzzle_glow[m], (39.5, 39.5), hand, 3.0, rot=a, mode="add", alpha=al)
        cv.sprite(art.muzzle[m], (39.5, 39.5), hand, 3.0, rot=a, alpha=al)


# ------------------------------------------------------------------------------------------------ the timelines
BAR_TIMES = [1.0, 1.7, 2.4, 3.1, 3.8]
STEP_AT = 0.55


def camera_for_bars(stage, t, bars_done, last_bar_t):
    st = STAGES[stage]
    chest = (st["origin"][0], st["origin"][1] - 20)
    if bars_done == 0:
        return VIEW_ZOOM, VIEW_FOCUS
    prev_z = VIEW_ZOOM if bars_done == 1 else BAR_ZOOM[bars_done - 2]
    prev_f = VIEW_FOCUS if bars_done == 1 else lerp2(VIEW_FOCUS, chest, BAR_FOCUS[bars_done - 2])
    k = ease_out_back((t - last_bar_t) / 0.22)
    z = lerp(prev_z, BAR_ZOOM[bars_done - 1], k)
    f = lerp2(prev_f, lerp2(VIEW_FOCUS, chest, BAR_FOCUS[bars_done - 1]), min(k, 1.0))
    return z, f


def shake(rng_, amp):
    return (rng_.uniform(-amp, amp), rng_.uniform(-amp, amp))


def success_timeline(stage):
    r = np.random.default_rng(5)
    st = STAGES[stage]
    hand = cell_to_world(st["origin"], st["muzzle"])
    full_len = math.hypot(CORE[0] - hand[0], CORE[1] - hand[1])
    shots = []
    T_END = 9.0
    release = BAR_TIMES[4] + 0.12
    travel = 0.35
    hit = release + 0.06 + travel
    dis_frames = 24
    dis_end = hit + dis_frames * 0.1
    t = 0.0
    while t < T_END:
        s = Shot()
        s.t = t
        bars = sum(1 for bt in BAR_TIMES if t >= bt)
        last = max([bt for bt in BAR_TIMES if t >= bt], default=0.0)
        # Jordan: staggered at 0 HP until the beam takes him
        if t < hit:
            s.god = ("hit", int(t / 0.25) % 2)
        elif t < dis_end:
            s.god = ("dis", min(int((t - hit) / 0.1), dis_frames - 1))
            s.runes_alpha = max(0.0, 1 - (t - hit) / 1.6)
        else:
            s.god = ("dis", dis_frames - 1)
            s.runes_alpha = 0.0
        # Burak
        if t < STEP_AT:
            s.burak = 0
        elif t < STEP_AT + 0.12:
            s.burak = 1
        elif t < release:
            s.burak = 2 + int((t - STEP_AT) / 0.09) % 3
            s.aura = ([0, 0, 1, 1, 2][max(bars, 1) - 1], int((t - STEP_AT) / 0.09) % 3) if bars >= 1 else None
        elif t < release + 0.05:
            s.burak = 5
        elif t < dis_end + 0.5:
            s.burak = 6 if t < release + 0.13 else 7 + int((t - release) / 0.06) % 2
        else:
            s.burak = 0
        # the ball
        if bars >= 1 and t < release:
            s.ball = (bars - 1, int(t / 0.07) % 4)
        elif STEP_AT + 0.12 <= t < BAR_TIMES[0]:
            s.ball = None
        # camera
        if t < release:
            s.zoom, s.focus = camera_for_bars(stage, t, bars, last)
            if bars >= 4:
                s.shake = shake(r, 3 + 3 * (bars - 3))
        else:
            z0, f0 = BAR_ZOOM[4], lerp2(VIEW_FOCUS, (st["origin"][0], st["origin"][1] - 20), 1.0)
            z1, f1 = st["release_view"]
            z2, f2 = st["dissolve_view"]
            if t < hit:
                k = min(1.0, (t - release) / 0.25)
                k = 1 - (1 - k) ** 3
                s.zoom, s.focus = lerp(z0, z1, k), lerp2(f0, f1, k)
                s.shake = shake(r, 14)
            elif t < dis_end:
                k = (t - hit) / (dis_end - hit)
                k = k * k * (3 - 2 * k)
                s.zoom, s.focus = lerp(z1, z2, k), lerp2(f1, f2, k)
                s.shake = shake(r, 9 * (1 - 0.6 * k))
            else:
                s.zoom, s.focus = z2, f2
                s.shake = shake(r, max(0.0, 4 * (1 - (t - dis_end) / 0.6)))
        # the shout
        if bars >= 1 and t < release + 1.1:
            idx = bars - 1
            px = SHOUT_SCALE[idx]
            pop = max(0.0, 1 - (t - last) / 0.15)
            if t >= release:
                pop = max(0.0, 1 - (t - release) / 0.15)
            s.word = (idx, px, pop, t >= release)
        if bars >= 1 and t < release:
            s.bars = bars
        # the beam
        if t >= release:
            fr = int((t - release) / 0.06)
            if t < release + 0.06:
                s.beam = dict(len=0, frame=fr, muzzle=0)
                s.flash = 0.55
            else:
                L = min(1.0, (t - release - 0.06) / travel) * full_len
                if t >= dis_end:
                    L = full_len + (t - dis_end) * 2600
                thick = 1.0
                al = 1.0
                if t >= dis_end + 0.35:
                    k = min(1.0, (t - dis_end - 0.35) / 0.45)
                    thick = max(0.0, 1 - k)
                    al = 1 - k * 0.5
                if thick > 0.02:
                    s.beam = dict(len=L, frame=fr, muzzle=1 if t < release + 0.12 else 2 + fr % 4, thick=thick, alpha=al)
                if release + 0.06 <= t < release + 0.12:
                    s.flash = 0.3
        if hit <= t < dis_end + 0.2:
            k = int((t - hit) / 0.07)
            s.impact = k if k < 4 else 4 + (k - 4) % 4
        if hit <= t < hit + 0.07:
            s.flash = 0.45
        # the core going: one hot flash
        core_pop = hit + 21 * 0.1
        if core_pop <= t < core_pop + 0.1:
            s.flash = 0.55
        shots.append(s)
        t += DT
    return shots


def fail_timeline(stage):
    """Three bars, the timer runs out, he lets it go anyway: a thin sputtering beam takes Jordan half way, cuts out,
    Burak staggers, and Jordan pulls himself back together in his own red (+5 on his bar)."""
    r = np.random.default_rng(9)
    st = STAGES[stage]
    hand = cell_to_world(st["origin"], st["muzzle"])
    full_len = math.hypot(CORE[0] - hand[0], CORE[1] - hand[1])
    shots = []
    timeout = 3.3
    release = timeout + 0.25
    travel = 0.35
    hit = release + 0.06 + travel
    beam_cut = hit + 0.75
    ref_start = hit
    ref_n = 16
    T_END = beam_cut + 2.6
    t = 0.0
    while t < T_END:
        s = Shot()
        s.t = t
        bars = min(3, sum(1 for bt in BAR_TIMES if t >= bt))
        last = max([bt for bt in BAR_TIMES[:3] if t >= bt], default=0.0)
        # Jordan
        if t < hit:
            s.god = ("hit", int(t / 0.25) % 2)
        else:
            k = int((t - ref_start) / 0.1)
            # forward to the half (0-8), hold on 8 while the beam sputters, then the red reform (9-15)
            if t < beam_cut:
                k = min(k, 8)
            else:
                k = min(9 + int((t - beam_cut) / 0.1), ref_n - 1)
            s.god = ("ref", k)
            if t >= beam_cut + (ref_n - 9) * 0.1:
                s.god = ("hover", int(t / 0.14) % 6)
        # Burak
        if t < STEP_AT:
            s.burak = 0
        elif t < STEP_AT + 0.12:
            s.burak = 1
        elif t < release:
            s.burak = 2 + int((t - STEP_AT) / 0.09) % 3
            if bars >= 1:
                s.aura = ([0, 0, 1][bars - 1], int((t - STEP_AT) / 0.09) % 3)
        elif t < release + 0.05:
            s.burak = 5
        elif t < beam_cut:
            s.burak = 6 if t < release + 0.13 else 7 + int((t - release) / 0.06) % 2
        elif t < beam_cut + 0.15:
            s.burak = 9
        elif t < beam_cut + 0.35:
            s.burak = 10
        elif t < beam_cut + 1.6:
            s.burak = 11
        else:
            s.burak = 0
        if bars >= 1 and t < release:
            s.ball = (bars - 1, int(t / 0.07) % 4)
        # camera
        if t < release:
            s.zoom, s.focus = camera_for_bars(stage, t, bars, last)
            if timeout <= t:
                s.shake = shake(r, 2)
        else:
            z0, f0 = BAR_ZOOM[2], lerp2(VIEW_FOCUS, (st["origin"][0], st["origin"][1] - 20), BAR_FOCUS[2])
            z1, f1 = st["release_view"]
            k = min(1.0, (t - release) / 0.3)
            k = 1 - (1 - k) ** 3
            s.zoom, s.focus = lerp(z0, z1, k), lerp2(f0, f1, k)
            if t < beam_cut:
                s.shake = shake(r, 4)
        # mash meter: three lit, then red as the timer runs out
        if bars >= 1 and t < release:
            s.bars = bars
            s.bars_red = t >= timeout and int((t - timeout) / 0.08) % 2 == 0
        # shout: SHIN, KU, HA ... then a deflated 'KEN...'
        if bars >= 1 and t < timeout:
            s.word = (bars - 1, SHOUT_SCALE[bars - 1], max(0.0, 1 - (t - last) / 0.15))
        elif release <= t < beam_cut + 0.6:
            s.word = (5, 3.5, 0.0, True)
        # the weak beam: thin, flickering, cut
        if t >= release:
            fr = int((t - release) / 0.06)
            if t < beam_cut:
                L = min(1.0, max(0.0, (t - release - 0.06) / travel)) * full_len
                flick = 0.5 + 0.08 * math.sin(t * 40) + (0.12 if (fr % 3 == 0) else 0.0)
                al = 1.0 if t < beam_cut - 0.3 else (0.35 if fr % 2 else 0.85)
                s.beam = dict(len=L, frame=fr, muzzle=1 if t < release + 0.12 else 2 + fr % 4, thick=flick, alpha=al)
            elif t < beam_cut + 0.4:
                s.fizzle = min(5, 2 + int((t - beam_cut) / 0.08))
        if hit <= t < beam_cut:
            k = int((t - hit) / 0.07)
            s.impact = 4 + k % 4
        # his bar: 0, then +5 back
        if t >= hit:
            back = beam_cut + (ref_n - 9) * 0.1
            fill = 0.0 if t < back else min(5 / 30, (t - back) / 0.4 * 5 / 30)
            s.god_bar = (fill, 1.0, 0.8 if back <= t < back + 0.1 else 0.0)
        if back_flash(t, beam_cut, ref_n):
            s.flash, s.flash_col = 0.16, (224, 40, 40)
        shots.append(s)
        t += DT
    return shots


def back_flash(t, beam_cut, ref_n):
    back = beam_cut + (ref_n - 9) * 0.1
    return back - 0.1 <= t < back + 0.03


def save_gif(frames, path):
    pal = [f.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, optimize=False,
                disposal=1)


def run(stage, take, kind):
    art = Art(take)
    shots = success_timeline(stage) if kind == "success" else fail_timeline(stage)
    frames = [render(art, stage, take, s) for s in shots]
    p = out_path("mocks", "mock_%s_%s_%s.gif" % (kind, stage, take))
    save_gif(frames, p)
    return frames, shots


if __name__ == "__main__":
    args = sys.argv[1:]
    jobs = [(a, b, c) for a in ("side", "back") for b in ("a", "b") for c in ("success",)] + [("side", "a", "fail")]
    if args:
        jobs = [tuple(args)]
    for job in jobs:
        frames, shots = run(*job)
        print(job, len(frames), "frames")
