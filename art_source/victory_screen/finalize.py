"""Write every victory-screen deliverable (+ per-frame PNGs for Aseprite import) into final/ and validate.
python finalize.py"""
import os, json
from cv import *
from pngio import read_png
import bg, player, banner, slots, icons, confetti

HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
OUT = HERE + '/final/'
FR = OUT + 'frames/'
os.makedirs(FR, exist_ok=True)

manifest = {}


def save(cv, name, frames=None, fw=None):
    cv.save(OUT + name + '.png')
    manifest[name] = dict(w=cv.w, h=cv.h, frames=len(frames) if frames else 1, frame_w=fw or cv.w)
    if frames:
        for i, f in enumerate(frames):
            f.save(FR + '%s_f%02d.png' % (name, i))


# background (player + contact shadow baked in)
save(bg.build(), 'victory_bg')
# player on its own (for layering over an animated crowd)
save(player.render(player.final_rows()), 'victory_player')
# banner (1x + 3x for StyleBoxTexture)
b = banner.build()
save(b, 'victory_banner')
banner.x3(b).save(OUT + 'victory_banner_3x.png')
manifest['victory_banner_3x'] = dict(w=b.w * 3, h=b.h * 3, frames=1, frame_w=b.w * 3)
# ladder
sl = slots.build()
save(slots.strip(sl), 'rank_slot', sl, slots.S)
ic = icons.build()
save(icons.strip(ic), 'rank_icons', ic, icons.S)
lk = slots.links()
save(slots.link_strip(), 'rank_link', lk, slots.LW)
# confetti overlay
cf = confetti.build()
save(confetti.strip(cf), 'victory_confetti', cf, confetti.W)

# ---------------- validation ----------------
ok = True
for name in manifest:
    w, h, px = read_png(OUT + name + '.png')
    alphas = {p[3] for row in px for p in row}
    cols = {'%02x%02x%02x' % p[:3] for row in px for p in row if p[3] == 255}
    bad = cols - DB
    opaque = alphas == {255}
    line = f"{name:22s} {w}x{h} frames={manifest[name]['frames']} alpha={sorted(alphas)} colours={len(cols)}"
    if bad:
        line += f" NON-DB32={sorted(bad)}"
        ok = False
    if not alphas <= {0, 255}:
        line += " PARTIAL-ALPHA"
        ok = False
    if name == 'victory_bg' and not opaque:
        line += " BG-NOT-OPAQUE"
        ok = False
    print(line)
json.dump(manifest, open(OUT + 'manifest.json', 'w'), indent=1)
print('ALL OK' if ok else 'PROBLEMS')
