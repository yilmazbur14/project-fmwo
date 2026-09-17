import sys
from weapons import *
from headrender import render_head
from headstrokes import STROKES
from legstamp import stamp_legs


def build(variant):
    cv = Canvas()
    cape(cv); stamp_legs(cv); flap(cv); tassets(cv); tasset_details(cv); belt(cv)
    tm = torso(cv); torso_details(cv, tm); belt_details(cv); gorget(cv)
    arm_right_back(cv)
    arm_left_back(cv)
    d, l1, l2 = pauldron(cv, ID); pauldron_details(cv, ID, d, l1, l2)
    if variant == 'sword':
        sword_blade(cv)
    d, l1, l2 = pauldron(cv, mirror); pauldron_details(cv, mirror, d, l1, l2)
    arm_right_front(cv)
    render_head(cv, STROKES)
    arm_left_front(cv, variant)
    if variant == 'sword':
        sword_hilt(cv)
    else:
        hammer_back(cv)
    fist_left(cv, variant)
    return cv


if __name__ == '__main__':
    from pngio import blank, paste, scale, write_png, read_png
    FL = (136, 180, 99, 255)
    for v in ('sword', 'hammer'):
        cv = build(v)
        cv.save(f'wip_{v}.png')
        cv.save(f'wip_{v}_8x.png', 8, FL)
    out = blank(10 + 2 * (96 * 3 + 10), 96 * 3 + 20, FL)
    for i, v in enumerate(('sword', 'hammer')):
        _, _, px = read_png(f'wip_{v}.png')
        paste(out, scale(px, 3), 10 + i * (96 * 3 + 10), 10)
    write_png('wip_3x.png', len(out[0]), len(out), out)
