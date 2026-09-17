"""Compose the 1920x1080 victory-screen mockup (scratch only).
All art is placed at base resolution (640x360) and the whole frame is scaled 3x, then text is
drawn with Pixelify Sans by text.ps1.
python mock.py outprefix [cleared=1]"""
import sys, os, subprocess
from cv import *
import bg, player, banner, slots, icons

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project/"

# ---------------- layout (base px; screen = x3) ----------------
TITLE = dict(cx=320, top=8)     # label box  y 8..48  (screen 24..144)
BANNER = (160, 50, 320, 46)     # x, y, w, h  (screen 480,150 960x138)
LADDER_Y = 234                  # slot row top (screen 702..822)
N_BOSSES = 5                    # Eric, Computah & Greyson, Carter & Josh, Liam & Bixby, Jordan
N_SLOTS = N_BOSSES + 1          # + the invite GOAL slot
SLOT, LINK = 40, 8
LADDER_W = N_SLOTS * SLOT + (N_SLOTS - 1) * LINK
LADDER_X = (640 - LADDER_W) // 2   # 6 slots: base 180 -> screen 540 .. 1380, centred on 960
BUTTON = (251, 280, 138, 42)    # base; screen 753,840 414x126


def nine_slice(src, m, WW, HH):
    """uniform-margin 9-slice of a Canvas (m in src px)."""
    out = Canvas(WW, HH)
    cw, ch = src.w - 2 * m, src.h - 2 * m
    CW, CH = WW - 2 * m, HH - 2 * m

    def mp(D, sc, dc):
        if D < m:
            return D
        if D >= m + dc:
            return D - (m + dc) + (m + sc)
        return m + min(sc - 1, (D - m) * sc // dc)

    for Y in range(HH):
        for X in range(WW):
            out.set(X, Y, src.get(mp(X, cw, CW), mp(Y, ch, CH)))
    return out


SCREENS = PROJ + "Assets/UI/Screens/"


def frame_of(strip, i, fw):
    return strip.crop(i * fw, 0, fw, strip.h)


def compose(cleared=1, with_ui=True, confetti_frame=0):
    """Composite ONLY from the shipped PNGs in Assets/UI/Screens (what the coder will get)."""
    cv = load(SCREENS + "victory_bg.png")
    if confetti_frame is not None:
        cv.blit(frame_of(load(SCREENS + "victory_confetti.png"), confetti_frame, 640), 0, 0)
    if not with_ui:
        return cv
    b = load(SCREENS + "victory_banner.png")
    cv.blit(banner.nine(b, BANNER[2], BANNER[3]), BANNER[0], BANNER[1])
    slot = load(SCREENS + "rank_slot.png")
    icon = load(SCREENS + "rank_icons.png")
    link = load(SCREENS + "rank_link.png")
    x = LADDER_X
    for i in range(N_SLOTS):
        if i == N_SLOTS - 1:
            state = 4 if cleared < N_BOSSES else 2   # invite: GOAL until the final boss falls
        elif i < cleared:
            state = 1                                # CLEARED
        elif i == cleared:
            state = 2                                # CURRENT (frame 3 = pulse)
        else:
            state = 0                                # LOCKED
        if state != 0:
            cv.blit(frame_of(icon, i, SLOT), x, LADDER_Y)
        cv.blit(frame_of(slot, state, SLOT), x, LADDER_Y)
        if i < N_SLOTS - 1:
            ls = 1 if i < cleared - 1 else (2 if i == cleared - 1 else 0)
            cv.blit(frame_of(link, ls, LINK), x + SLOT, LADDER_Y)
        x += SLOT + LINK
    btn = load(PROJ + "Assets/UI/ui_button.png")
    cv.blit(nine_slice(btn, 8, BUTTON[2], BUTTON[3]), BUTTON[0], BUTTON[1])
    return cv


def upscale3(cv):
    out = Canvas(cv.w * 3, cv.h * 3)
    for y in range(cv.h):
        row = cv.p[y]
        for k in range(3):
            orow = out.p[y * 3 + k]
            for x in range(cv.w):
                c = row[x]
                orow[x * 3] = c
                orow[x * 3 + 1] = c
                orow[x * 3 + 2] = c
    return out


def text_spec(cleared):
    bx, by, bw, bh = [v * 3 for v in BANNER]
    tx = bx + 117
    lines = [
        # x|y|size|colour|align|shadow|shadowOffset|text
        "960|30|99|fbf236|C|-|0|Victory!",
        f"{tx}|{by + 22}|33|fbf236|L|-|0|SYSTEM",
        f"{tx + 150}|{by + 22}|33|9badb7|L|-|0|Today at 11:59 PM",
        f"{tx}|{by + 72}|33|ffffff|L|-|0|@newcomer ranked up to @member!",
        f"960|{BUTTON[1] * 3 + 30}|55|ffffff|C|-|0|NEXT BOSS",
    ]
    return lines


if __name__ == '__main__':
    pre = sys.argv[1]
    cleared = 1
    for a in sys.argv[2:]:
        if a.startswith('cleared='):
            cleared = int(a.split('=')[1])
    cv = compose(cleared)
    cv.save(pre + '_base.png')
    big = upscale3(cv)
    big.save(pre + '_notext.png')
    spec = pre + '_text.txt'
    open(spec, 'w').write('\n'.join(text_spec(cleared)) + '\n')
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', HERE + '/text.ps1',
                        '-In', os.path.abspath(pre + '_notext.png'), '-Out', os.path.abspath(pre + '.png'),
                        '-SpecFile', os.path.abspath(spec)], capture_output=True, text=True)
    print(r.stdout, r.stderr)
