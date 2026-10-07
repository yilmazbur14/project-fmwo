"""Still sheets for the review: the stagings x takes compare, Burak's frames, the beam takes side by side, the
per-bar zoom, and the shout placement frame. Writes into approval/mocks only."""
import sys
sys.argv = ["mock.py"]
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *
import mock
import energy as E
import export

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    FONT_B = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 22)
except Exception:
    FONT = FONT_B = ImageFont.load_default()

BG = (20, 14, 34)


def label(img, text, xy=(10, 8), font=None, fill=(255, 255, 255)):
    d = ImageDraw.Draw(img)
    x, y = xy
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            d.text((x + dx, y + dy), text, font=font or FONT, fill=(0, 0, 0))
    d.text(xy, text, font=font or FONT, fill=fill)
    return img


def frame_at(stage, take, t, kind="success"):
    art = mock.Art(take)
    shots = mock.success_timeline(stage) if kind == "success" else mock.fail_timeline(stage)
    i = min(int(round(t * mock.FPS)), len(shots) - 1)
    return mock.render(art, stage, take, shots[i])


def compare():
    """2x2: staging A / B down, take A / B across, at the hit (the beam on him, the dissolve starting)."""
    tiles = []
    for stage, sname in (("side", "STAGING A - side-on"), ("back", "STAGING B - from behind")):
        row = []
        for take, tname in (("a", "TAKE A - blue-white (recommended)"), ("b", "TAKE B - HYPE gold/pink")):
            im = frame_at(stage, take, 4.85).convert("RGB")
            label(im, "%s  |  %s" % (sname, tname))
            row.append(im)
        tiles.append(row)
    w, h = 960, 540
    sheet = Image.new("RGB", (w * 2 + 8, h * 2 + 8), (0, 0, 0))
    for j, row in enumerate(tiles):
        for i, im in enumerate(row):
            sheet.paste(im, (i * (w + 8), j * (h + 8)))
    save_png(sheet, "mocks", "compare_stagings_x_takes.png")


def charge_compare():
    """The same at bar 5, just before the release: the close-up on him and the ball."""
    tiles = []
    for stage in ("side", "back"):
        for take in ("a", "b"):
            im = frame_at(stage, take, 3.87).convert("RGB")
            label(im, "%s / take %s - bar 5 (KEN!!!!), the frame before the release" % ("A side" if stage == "side" else "B back", take.upper()))
            tiles.append(im)
    sheet = Image.new("RGB", (960 * 2 + 8, 540 * 2 + 8), (0, 0, 0))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % 2) * 968, (k // 2) * 548))
    save_png(sheet, "mocks", "compare_bar5_closeup.png")


def burak_frames():
    S = 6
    names = export.ORDER
    rows = []
    for stage in ("side", "back"):
        strip_img = Image.open(APPROVAL + "/player/player_final_beam_%s.png" % stage).convert("RGBA")
        z = zoomed(strip_img, S, BG + (255,)).convert("RGB")
        top = Image.new("RGB", (z.width, 28), BG)
        label(top, "STAGING %s  (48x48 cells, his own 7 colours, centred on MainPlayer's origin)" %
              ("A - side-on, facing right" if stage == "side" else "B - from behind"), (6, 4))
        lab = Image.new("RGB", (z.width, 22), BG)
        for i, n in enumerate(names):
            label(lab, "%d %s" % (i, n), (i * 48 * S + 6, 2))
        col = Image.new("RGB", (z.width, top.height + z.height + lab.height), BG)
        col.paste(top, (0, 0)); col.paste(z, (0, top.height)); col.paste(lab, (0, top.height + z.height))
        rows.append(col)
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows) + 10), BG)
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height + 10
    save_png(sheet, "mocks", "compare_burak_frames_6x.png")


def beam_takes():
    """Each take's pieces on the void colour, the beam laid out straight, at 2x."""
    out = []
    for take, name in (("a", "TAKE A - classic blue-white (recommended)"), ("b", "TAKE B - HYPE white/yellow/pink")):
        L = 64 + 32 * 6
        cv = Canvas(L + 100, 150, render_scale=1.0)
        cv.fill(BG)
        cv.set_camera(1.0, ((L + 100) / 2, 75))
        art = mock.Art(take)
        b = None
        # lay it out along +x from (14, 75)
        st = dict(mock.STAGES["side"])
        hand = (14.0, 75.0)
        a = 0.0
        f = 0
        at = lambda u: (hand[0] + u, hand[1])
        cv.sprite(art.start_glow[f], (0, E.BODY_GLOW_H / 2), hand, 1.0, mode="add")
        n = 6
        n = 5
        for k in range(n):
            cv.sprite(art.body_glow[f], (0, E.BODY_GLOW_H / 2), at(64 + 32 * k), 1.0, mode="add")
        cv.sprite(art.start[f], (0, E.BODY_H / 2), hand, 1.0)
        for k in range(n):
            cv.sprite(art.body[f], (0, E.BODY_H / 2), at(64 + 32 * k), 1.0)
            cv.sprite(art.spiral[f], (0, E.BODY_H / 2), at(64 + 32 * k), 1.0, mode="add")
        cv.sprite(art.head_glow[f], (78, E.HEAD / 2), at(L), 1.0, mode="add")
        cv.sprite(art.head[f], (78, E.HEAD / 2), at(L), 1.0)
        cv.sprite(art.muzzle_glow[3], (39.5, 39.5), hand, 1.0, mode="add")
        cv.sprite(art.muzzle[3], (39.5, 39.5), hand, 1.0)
        beam = cv.image()
        # balls 1-5, impact, the god's crack colour
        cv2 = Canvas(64 * 5 + E.IMPACT * 2 + 20, E.IMPACT, render_scale=1.0)
        cv2.fill(BG)
        cv2.set_camera(1.0, (cv2.w / 2, cv2.h / 2))
        for s in range(5):
            p = (32 + 64 * s - cv2.w / 2 + cv2.w / 2, E.IMPACT / 2)
            cv2.sprite(art.ball_glow[s][0], (32, 32), p, 1.0, mode="add")
            cv2.sprite(art.ball[s][0], (32, 32), p, 1.0)
        for k, idx in enumerate((1, 5)):
            p = (64 * 5 + 10 + E.IMPACT / 2 + k * E.IMPACT, E.IMPACT / 2)
            cv2.sprite(art.impact_glow[idx], (E.IMPACT / 2, E.IMPACT / 2), p, 1.0, mode="add")
            cv2.sprite(art.impact[idx], (E.IMPACT / 2, E.IMPACT / 2), p, 1.0)
        parts = cv2.image()
        S = 2
        top = Image.new("RGB", (max(beam.width, parts.width) * S, 30), BG)
        label(top, name, (8, 6), FONT_B)
        col = Image.new("RGB", (top.width, 30 + beam.height * S + parts.height * S + 10), BG)
        col.paste(top, (0, 0))
        col.paste(beam.resize((beam.width * S, beam.height * S), Image.NEAREST), (0, 30))
        col.paste(parts.resize((parts.width * S, parts.height * S), Image.NEAREST), (0, 30 + beam.height * S + 10))
        out.append(col)
    sheet = Image.new("RGB", (max(o.width for o in out), sum(o.height for o in out) + 12), BG)
    y = 0
    for o in out:
        sheet.paste(o, (0, y)); y += o.height + 12
    save_png(sheet, "mocks", "compare_beam_takes_2x.png")


def bar_steps():
    """The camera a bar: the wide shot, then bars 1-5, staging by staging (take A)."""
    for stage in ("side", "back"):
        times = [0.3] + [bt + 0.08 if k == 4 else bt + 0.3 for k, bt in enumerate(mock.BAR_TIMES)]
        ims = []
        for k, t in enumerate(times):
            im = frame_at(stage, "a", t).convert("RGB").resize((480, 270), Image.LANCZOS)
            label(im, "start (0 HP)" if k == 0 else "bar %d  zoom %.2f" % (k, mock.BAR_ZOOM[k - 1]))
            ims.append(im)
        sheet = Image.new("RGB", (480 * 3 + 8, 270 * 2 + 4), (0, 0, 0))
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % 3) * 484, (k // 3) * 274))
        save_png(sheet, "mocks", "bars_zoom_steps_%s.png" % stage)


def shout_placement():
    """Where the syllable sits: anchored in the world off his origin (so it rides the zoom), centred there, drawn
    in screen px at SHOUT_SCALE[bar]; clamped 16 px inside the screen."""
    ims = []
    for stage in ("side", "back"):
        for t, what in ((mock.BAR_TIMES[2] + 0.2, "bar 3: HA"), (mock.BAR_TIMES[4] + 0.75, "release: KEN!!!!")):
            im = frame_at(stage, "a", t).convert("RGB")
            st = mock.STAGES[stage]
            art = mock.Art("a")
            shots = mock.success_timeline(stage)
            s = shots[int(round(t * mock.FPS))]
            cv = Canvas()
            cv.set_camera(s.zoom, (s.focus[0] + s.shake[0], s.focus[1] + s.shake[1]))
            o = cv.world_to_screen(st["origin"])
            idx = 2 if "HA" in what else 4
            off = st["ken"] if idx == 4 else st["shout"]
            a = cv.world_to_screen((st["origin"][0] + off[0], st["origin"][1] + off[1]))
            d = ImageDraw.Draw(im)
            d.line([tuple(o), tuple(a)], fill=(255, 80, 200), width=2)
            d.ellipse([o[0] - 4, o[1] - 4, o[0] + 4, o[1] + 4], outline=(255, 80, 200), width=2)
            d.ellipse([a[0] - 5, a[1] - 5, a[0] + 5, a[1] + 5], outline=(255, 255, 0), width=2)
            idx = 2 if "HA" in what else 4
            px = mock.SHOUT_SCALE[idx] * 0.5
            wimg = mock.word_trim(art.words[idx])
            w, h = wimg.width * px, wimg.height * px
            d.rectangle([a[0] - w / 2, a[1] - h / 2, a[0] + w / 2, a[1] + h / 2], outline=(255, 255, 0), width=1)
            label(im, "STAGING %s - %s" % ("A" if stage == "side" else "B", what), (10, 8), FONT_B)
            label(im, "anchor = his origin + (%d, %d) world px; word centred on it; %.1f screen px a texel @1080p"
                  % (off[0], off[1], mock.SHOUT_SCALE[idx]), (10, 38))
            label(im, "SHIN 4.0 / KU 4.5 / HA 5.0 / DO 5.5 / KEN!!!! 7.0 - pop 1.35x -> 1x over 0.15 s", (10, 58))
            ims.append(im)
    sheet = Image.new("RGB", (960 * 2 + 8, 540 * 2 + 8), (0, 0, 0))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % 2) * 968, (k // 2) * 548))
    save_png(sheet, "mocks", "shout_placement.png")


if __name__ == "__main__":
    compare()
    charge_compare()
    burak_frames()
    beam_takes()
    bar_steps()
    shout_placement()
    print("stills done")
