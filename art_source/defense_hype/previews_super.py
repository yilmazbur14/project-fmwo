"""Review previews for the supercharged impact extras: GIFs, an in-fight mockup and a before/after.
  python previews_super.py [mock] [gifs]
Outputs go to DH_PREVIEWS (the scratchpad super_impact folder)."""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *
from gifio import write_gif
import previews as PV
import super_impact as SI

OUT = PREVIEWS.rstrip('/') + '/'
RAYS = from_png(PROJ + 'Assets/Effects/super_impact_rays.png')
RING = from_png(PROJ + 'Assets/Effects/super_impact_ring.png')
RAYS_F = [crop(RAYS, i * SI.RW, 0, SI.RW, SI.RH) for i in range(5)]
RING_F = [crop(RING, i * SI.GW, 0, SI.GW, SI.GH) for i in range(6)]

ERIC_CENTRE_X, ERIC_FEET = 1111, PV.EFEET          # where the blast ring rolls out from
RING_WORLD_SCALE = 3                                # world-space scale; the finisher's 1.5x camera makes it ~4.5x on screen


def contact_screen():
    ix = PV.PX + (27 - 24) * 2 + PV.IMPACT_OFFSET[0]
    iy = PV.PY - 96 + 14 * 2 + PV.IMPACT_OFFSET[1]
    return PV.world_to_screen(ix, iy)


def scene(ray_f=None, ring_f=None, imp_f=1, upc_f=5, hud=True):
    """world: arena + blast ring (under everyone) + Eric + burst + player; then the camera zoom;
    then the screen-space ray overlay, then the HUD"""
    world = PV.arena()
    if ring_f is not None:
        r = RING_F[ring_f]
        PV.paste(world, r, ERIC_CENTRE_X - SI.GCX * RING_WORLD_SCALE,
                 ERIC_FEET - SI.GCY * RING_WORLD_SCALE, RING_WORLD_SCALE)
    er = PV.eric(27)
    PV.paste(world, er, 1000 - (255 - 165) * 3, PV.EFEET - 192 * 3, 3, flip=True)
    if imp_f is not None:
        ix = PV.PX + (27 - 24) * 2 + PV.IMPACT_OFFSET[0]
        iy = PV.PY - 96 + 14 * 2 + PV.IMPACT_OFFSET[1]
        imp = crop(from_png(PROJ + 'Assets/Effects/uppercut_impact_super.png'), imp_f * 96, 0, 96, 96)
        PV.paste(world, imp, ix - 96, iy - 96, 2)
    up = crop(from_png(PROJ + 'Assets/Characters/MainPlayer/player_uppercut_super.png'), upc_f * 48, 0, 48, 64)
    PV.paste(world, up, PV.PX - 48, PV.PY - 96, 2)
    img = PV.zoom_view(world, PV.CAMX, PV.CAMY)
    if ray_f is not None:
        sx, sy = contact_screen()
        PV.paste(img, RAYS_F[ray_f], sx - SI.RCX * 3, sy - SI.RCY * 3, 3)
    if hud:
        PV.draw_hearts(img, 5)
        PV.draw_stamina(img, 0.6)
        PV.draw_hype(img, 1.0, full_frame=0)
    return img


def mocks():
    img = scene(ray_f=0, ring_f=1, imp_f=1, upc_f=5)
    PV.save(img, 'mockup_super_contact_rays_ring.png')
    later = scene(ray_f=2, ring_f=3, imp_f=3, upc_f=6)
    PV.save(later, 'mockup_super_contact_frame3.png')
    # before / after, half scale side by side
    before = scene(ray_f=None, ring_f=None, imp_f=1, upc_f=5)
    cmp_img = PV.rgb(1920, 540, (30, 30, 40))
    a = [row[::2] for row in before[::2]]
    b = [row[::2] for row in img[::2]]
    for y in range(540):
        cmp_img[y][:960] = a[y]
        cmp_img[y][960:] = b[y]
    PV.text(cmp_img, 'CURRENT SUPER CONTACT', 20, 16, 4, (255, 255, 255))
    PV.text(cmp_img, 'WITH RAYS + BLAST RING', 980, 16, 4, (255, 240, 120))
    PV.save(cmp_img, 'mockup_before_after.png')


def gifs():
    # rays alone, on the arena floor colour, at half of the in-game size (3x art shown at 1.5x here)
    frames, durs = [], []
    for f in range(5):
        img = PV.rgb(SI.RW, SI.RH, (136, 180, 99))
        PV.paste(img, RAYS_F[f], 0, 0, 1)
        frames.append(img)
        durs.append(max(2, SI.RAY_DURATIONS_MS[f] // 10))
    frames.append(PV.rgb(SI.RW, SI.RH, (136, 180, 99)))
    durs.append(40)
    write_gif(OUT + 'gif_super_impact_rays_1x.gif', frames, durs)
    print('wrote gif_super_impact_rays_1x.gif')
    # ring alone at 2x on the floor
    frames, durs = [], []
    for f in range(6):
        img = PV.rgb(SI.GW * 2 + 40, SI.GH * 2 + 40, (136, 180, 99))
        PV.paste(img, RING_F[f], 20, 20, 2)
        frames.append(img)
        durs.append(max(2, SI.RING_DURATIONS_MS[f] // 10))
    frames.append(PV.rgb(SI.GW * 2 + 40, SI.GH * 2 + 40, (136, 180, 99)))
    durs.append(40)
    write_gif(OUT + 'gif_super_impact_ring_2x.gif', frames, durs)
    print('wrote gif_super_impact_ring_2x.gif')
    # the whole contact in scene, half resolution
    seq = [(None, None, 0, 4, 4), (0, 0, 0, 5, 3), (0, 1, 1, 5, 5), (1, 2, 2, 6, 6), (2, 3, 3, 7, 7),
           (3, 4, 4, 7, 8), (4, 5, 5, 8, 9), (None, None, 6, 9, 10), (None, None, None, 9, 40)]
    frames, durs = [], []
    for (rf, gf, imf, uf, d) in seq:
        img = scene(ray_f=rf, ring_f=gf, imp_f=imf, upc_f=uf)
        frames.append([row[::2] for row in img[::2]])
        durs.append(d)
    write_gif(OUT + 'gif_super_contact_full.gif', frames, durs)
    print('wrote gif_super_contact_full.gif')


if __name__ == '__main__':
    which = [a for a in sys.argv[1:] if not a.startswith('--')] or ['mock', 'gifs']
    if 'mock' in which:
        mocks()
    if 'gifs' in which:
        gifs()
