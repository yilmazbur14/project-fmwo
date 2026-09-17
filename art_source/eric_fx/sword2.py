"""Redesign greatsword (eric_redesign_sword.png) rebuilt straight, tip up, as a 29x118 grid V_UP.
Blade body rows are the reference rows un-sheared pixel for pixel (pits, chips, thickness strip kept);
the tip, crossguard, grip and pommel are hand-ruled in the reference palette."""
from common import *

REF = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_sword.png'
MAP = {(0, 0, 0, 255): 'K', (163, 168, 174, 255): 'A', (212, 216, 220, 255): 'B', (124, 129, 135, 255): 'C',
       (92, 96, 103, 255): 'D', (65, 68, 75, 255): 'E', (43, 45, 51, 255): 'F'}
W = 29          # crossguard width; blade occupies cols 4..24, axis col 14
BL = 4          # blade left col

TIP = [  # 21 wide (cols 4..24), rows 0..9, ref palette letters
    "..........KKKKK......",
    ".........KACCCFK.....",
    "........KABCCCEFK....",
    ".......KABCCCCCEFK...",
    "......KABCCCCCCDEFK..",
    ".....KABCCCCCCCDFEFK.",
    "....KABCCCCCCCCDFEEFK",
    "...KABACCCCCCCCDFEEFK",
    "..KABACCCCCCCCCDFEEFK",
    ".KABACCCCCCCCCCDFEEFK",
]
GUARD = [
    ".KKKKKKKKKKKKKKKKKKKKKKKKKKK.",
    "KBBBBBAAAAAAAAAAAAAAAAAAAAADK",
    "KBAAACCCCCCCCCCCCCCCCCCCCCDEK",
    "KACCCCCCCDCCCCCCCCCCCCDCCDDEK",
    "KCCCCCCCCCCCCCCCCCCCCCCCDDEEK",
    "KDDDDDDDDDDDDDDDDDDDDDEEEEEFK",
    ".KKKKKKKKKKKKKKKKKKKKKKKKKKK.",
]
GRIP_ROWS = 17
POMMEL = [
    "..KKKKK..",
    ".KBBAADK.",
    "KBBAAADDK",
    "KAAADDDEK",
    ".KDDDEEK.",
    "..KKKKK..",
]

def ref_body_rows():
    w, h, px = read_png(REF)
    rows = []
    for y in range(12, 87):
        xr = 22 + (y - 13) // 5            # right outline column of the slanted blade on this row
        row = ''
        for c in range(21):
            p = px[y][xr - 20 + c]
            row += MAP.get(tuple(p), '.') if p[3] else '.'
        # anything left of the left outline is background (arm/cape never overlaps here)
        rows.append(row)
    return rows

def build_up():
    body = ref_body_rows()                  # 75 rows
    # the reference is slanted ~11deg, so its true blade length is ~88px: add 3 clean repeat rows
    clean = "KABACCCCCCCCCCCDFEEFK"
    for i in (62, 44, 22):
        body.insert(i, clean)
    assert len(body) == 78
    V = []
    for r in TIP:
        V.append('.' * BL + r + '.' * (W - BL - 21))
    for r in body:
        V.append('.' * BL + r + '.' * (W - BL - 21))
    V += GUARD
    for i in range(GRIP_ROWS):
        band = ('orm', 'orm', 'rrm', 'rms')[i % 4]
        V.append('.' * 12 + 'K' + band + 'K' + '.' * (W - 17))
    for r in POMMEL:
        V.append('.' * 10 + r + '.' * (W - 19))
    assert len(V) == 118 and all(len(r) == W for r in V), [len(r) for r in V]
    return V

if __name__ == '__main__':
    V = build_up()
    save_grid('v2/sword_up.txt', V)
    view('v2/sword_up_8x.png', V, 8)
    for i, r in enumerate(V): print(f'{i:3d} {r}')
