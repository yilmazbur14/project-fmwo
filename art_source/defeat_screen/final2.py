"""v2 final: new jeering stands + unchanged upper layers (rendered standalone and
proven identical to the approved composite) + house-style banner icon.
python final2.py"""
import os
from lib import *
import scene
import props
import compose as cp
import banner as bn
import stands2

APPROVED_BG = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/Screens/defeat_bg.png"
APPROVED_STANDS = 'out/final/layer_stands.png'
OUT = 'out/final2/'
os.makedirs(OUT, exist_ok=True)


def over(layers, w=640, h=360):
    im = Img(w, h)
    for L in layers:
        im.blit(L, 0, 0)
    return im


def upper_layers():
    ring = Img(640, 360)
    scene.canvas(ring)
    scene.ropes_side(ring)
    scene.ropes_far(ring)
    scene.posts(ring)
    # player + cast shadow (cast shadow reads the ring pixels it darkens)
    player = Img(640, 360)
    tmp = ring.copy()
    pimg, union = cp.player_layer()
    ox, oy = cp.PLAYER_AT
    before = tmp.copy()
    cp.cast_shadow(tmp, union, ox, oy)
    for y in range(360):
        for x in range(640):
            if tmp.p[y][x] != before.p[y][x]:
                player.p[y][x] = tmp.p[y][x]
    for (x, y) in union | outline_of(union):
        c = pimg.get(x, y)
        if c is not None:
            player.set(ox + x, oy + y, c)
    # boss shadow: every masked pixel, darkened from ring+player beneath
    base = over([ring, player])
    shadow = Img(640, 360)
    mask = props.boss_shadow_mask(522, 178, 1.75, 1.9, 0.25)
    for (x, y) in mask:
        c = base.get(x, y)
        if c is not None:
            shadow.set(x, y, props.DARKEN.get(c, NAVY))
    pennants = Img(640, 360)
    props.pennant(pennants, 20, 6, 52, 64, props.pennant_icon)
    props.pennant(pennants, 568, 6, 52, 64, props.pennant_channel)
    return [('ring', ring), ('player', player), ('boss_shadow', shadow), ('pennants', pennants)]


def main():
    ups = upper_layers()
    approved = load(APPROVED_BG)
    old_stands = load(APPROVED_STANDS)
    uncovered = [(x, y) for y in range(360) for x in range(640) if all(L.p[y][x] is None for _, L in ups)]
    # 1) prove the standalone upper layers reproduce the approved screen exactly
    re_approved = over([old_stands] + [L for _, L in ups])
    m1 = sum(1 for y in range(360) for x in range(640) if re_approved.p[y][x] != approved.p[y][x])
    print('upper layers over OLD stands vs approved defeat_bg.png: %d differing px' % m1)
    # 2) new stands
    stands = stands2.to_img(stands2.build_stands(4))
    new = over([stands] + [L for _, L in ups])
    changed = [(x, y) for y in range(360) for x in range(640) if new.p[y][x] != approved.p[y][x]]
    covered_changes = [(x, y) for (x, y) in changed if any(L.p[y][x] is not None for _, L in ups)]
    print('new composite: %d px changed, %d of them outside the visible stands (must be 0)'
          % (len(changed), len(covered_changes)))
    print('visible stands px:', len(uncovered))
    print('non-DB32:', sorted(new.check_db32()))
    new.save(OUT + 'defeat_bg.png')
    stands.save(OUT + 'layer_stands.png')
    for name, L in ups:
        L.save(OUT + 'layer_%s.png' % name)
    chk = over([load(OUT + 'layer_stands.png')] + [load(OUT + 'layer_%s.png' % n) for n, _ in ups])
    print('layer PNG re-composite mismatches:', sum(1 for y in range(360) for x in range(640) if chk.p[y][x] != new.p[y][x]))
    # banner (house-style icon); size + margins unchanged
    b = bn.build('b')
    print('banner size', b.w, b.h, 'margins', (bn.ML, bn.MT, bn.MR, bn.MB), '9-slice problems:',
          bn.nine_slice_ok(b, bn.ML, bn.MT, bn.MR, bn.MB))
    b.save(OUT + 'defeat_banner.png')
    b3 = b.scaled(3)
    print('banner_3x size', b3.w, b3.h, '9-slice@3x problems:',
          bn.nine_slice_ok(b3, bn.ML * 3, bn.MT * 3, bn.MR * 3, bn.MB * 3))
    b3.save(OUT + 'defeat_banner_3x.png')
    zoom_save(new, OUT + 'defeat_bg_2x.png', 2)


if __name__ == '__main__':
    main()
