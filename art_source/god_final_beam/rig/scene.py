"""The god fight's void as the game draws it (JordanGodLayout / VoidArena / JordanGodScript numbers)."""
import numpy as np
from common import *

VIEW_ZOOM = 2.0 / 3.0
VIEW_FOCUS = (960.0, 804.0)
GOD_POINT = (960.0, 600.0)
CORE = (960.0, 304.0)          # GOD_POINT + RUNES_OFFSET (0,-296)
PLAYER_START = (620.0, 761.0)  # VOID_PLAYER_MARK - (0,39)

VOID = repo_img("Assets/Environment/Void/void_bg.png")
HOVER = repo_img("Assets/Characters/Jordan/God/jordan_god_hover.png")
HIT = repo_img("Assets/Characters/Jordan/God/jordan_god_hit.png")
AURA = repo_img("Assets/Characters/Jordan/God/jordan_god_aura.png")
HIT_AURA = repo_img("Assets/Characters/Jordan/God/jordan_god_hit_aura.png")
RUNES = repo_img("Assets/Characters/Jordan/God/jordan_god_runes.png")
P4 = repo_img("Assets/Characters/MainPlayer/player_4dir_sheet.png")


def cell(sheet, i, w, h, row=0):
    return sheet.crop((i * w, row * h, i * w + w, row * h + h))


def god_hover(i):
    return cell(HOVER, i % 6, 320, 224)


def god_hit(i):
    return cell(HIT, i % 2, 320, 224)


def god_aura(i):
    return cell(AURA, i % 6, 336, 232)


def god_hit_aura(i):
    return cell(HIT_AURA, i % 2, 336, 232)


def runes(i):
    return cell(RUNES, i % 36, 192, 192)


def burak(col, row):
    return cell(P4, col, 32, 32, row)


def draw_void(cv):
    cv.screen_image(VOID, 3.0)


def draw_runes(cv, t, alpha=1.0):
    cv.sprite(runes(int(t / 0.1)), (96, 96), CORE, 3.0, alpha=alpha)


def draw_god(cv, body, aura=None, alpha=1.0, aura_alpha=1.0, offset=(0, 0)):
    p = (GOD_POINT[0] + offset[0], GOD_POINT[1] + offset[1])
    cv.sprite(body, (160, 223), p, 3.0, alpha=alpha)
    if aura is not None:
        cv.sprite(aura, (168, 223), p, 3.0, mode="add", alpha=aura_alpha)


if __name__ == "__main__":
    cv = Canvas()
    cv.set_camera(VIEW_ZOOM, VIEW_FOCUS)
    draw_void(cv)
    draw_runes(cv, 0)
    draw_god(cv, god_hover(0), god_aura(0))
    cv.sprite(burak(0, 1), (16, 16), PLAYER_START, 3.0)
    img = cv.image()
    img.save(WORK + "/validate_render.png")
    cap = Image.open("C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/jordan_puppet_master/stills_B/03_pulled_back.png").convert("RGB")
    a = np.asarray(img, np.int32); b = np.asarray(cap, np.int32)
    d = np.abs(a - b).sum(-1)
    print("mean abs diff", d.mean(), "pixels >30:", (d > 30).mean())
    # mask out HUD regions
    m = np.ones_like(d, bool); m[:60, 300:660] = False; m[470:, :150] = False; m[470:, 760:] = False
    print("non-HUD mean diff", d[m].mean(), "pixels >30:", (d[m] > 30).mean())
    Image.fromarray(np.clip(d * 3, 0, 255).astype(np.uint8)).save(WORK + "/validate_diff.png")
