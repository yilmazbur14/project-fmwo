"""Final build: composite + per-layer PNGs for the layered .aseprite, banner 1x/3x,
star frames. Writes into out/final/.  python final.py"""
import os
from lib import *
import scene
import props
import compose as cp
import banner as bn
import stars as st
from crowd import crowd_rows

OUT = 'out/final/'
os.makedirs(OUT, exist_ok=True)


def snapshot(im):
    return [row[:] for row in im.p]


def diff_layer(prev, cur):
    L = Img(scene.W, scene.H)
    for y in range(scene.H):
        for x in range(scene.W):
            if cur[y][x] != prev[y][x]:
                L.p[y][x] = cur[y][x]
    return L


def build_layers():
    im = Img(scene.W, scene.H)
    scene.backdrop(im)
    crowd_rows(im, cp.FAR_ROWS[:3], seed=5)
    crowd_rows(im, cp.FAR_ROWS[3:], seed=6, spill=(320, 110))
    cp.fade_top(im, 46, 72)
    props.sign(im, 188, 58, 'GG EZ', card=GREY_L, shade=GREY)
    props.sign(im, 458, 54, 'L', card=GREY_L, shade=GREY)
    cp.side_crowd(im)
    layers = []
    s0 = snapshot(im)
    base = Img(scene.W, scene.H)
    base.p = snapshot(im)
    layers.append(('stands', base))

    scene.canvas(im)
    scene.ropes_side(im)
    scene.ropes_far(im)
    scene.posts(im)
    s1 = snapshot(im)
    layers.append(('ring', diff_layer(s0, s1)))

    pimg, union = cp.player_layer()
    ox, oy = cp.PLAYER_AT
    cp.cast_shadow(im, union, ox, oy)
    for (x, y) in union | outline_of(union):
        c = pimg.get(x, y)
        if c is not None:
            im.set(ox + x, oy + y, c)
    s2 = snapshot(im)
    layers.append(('player', diff_layer(s1, s2)))

    sm = props.boss_shadow_mask(522, 178, 1.75, 1.9, 0.25)
    props.apply_shadow(im, sm)
    s3 = snapshot(im)
    layers.append(('boss_shadow', diff_layer(s2, s3)))

    props.pennant(im, 20, 6, 52, 64, props.pennant_icon)
    props.pennant(im, 568, 6, 52, 64, props.pennant_channel)
    s4 = snapshot(im)
    layers.append(('pennants', diff_layer(s3, s4)))
    return im, layers


def main():
    im, layers = build_layers()
    # sanity: must match the tuned compose.build() output
    ref = cp.build('final')
    mism = sum(1 for y in range(scene.H) for x in range(scene.W) if ref.p[y][x] != im.p[y][x])
    print('composite vs compose.build mismatches:', mism)
    im.save(OUT + 'defeat_bg.png')
    # re-composite layers to verify
    chk = Img(scene.W, scene.H)
    for name, L in layers:
        L.save(OUT + 'layer_%s.png' % name)
        chk.blit(L, 0, 0)
    mism2 = sum(1 for y in range(scene.H) for x in range(scene.W) if chk.p[y][x] != im.p[y][x])
    print('layer re-composite mismatches:', mism2)
    print('bg non-DB32 colours:', sorted(im.check_db32()))
    # banner
    b = bn.build('b')
    print('banner 9-slice problems:', bn.nine_slice_ok(b, bn.ML, bn.MT, bn.MR, bn.MB))
    b.save(OUT + 'defeat_banner.png')
    b.scaled(3).save(OUT + 'defeat_banner_3x.png')
    # stars
    strip = st.strip()
    strip.save(OUT + 'defeat_stars.png')
    for k in range(4):
        st.frame(k).save(OUT + 'stars_f%d.png' % k)
    print('stars strip', strip.w, strip.h)


if __name__ == '__main__':
    main()
