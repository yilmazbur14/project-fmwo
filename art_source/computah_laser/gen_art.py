import sys, os
from pngio import *

PAL = {
    '.': (0, 0, 0, 0),
    'O': (66, 10, 20, 255),
    'R': (172, 50, 50, 255),
    'P': (212, 150, 156, 255),
    'L': (248, 212, 216, 255),
    'W': (255, 255, 255, 255),
}

def grid(lines):
    return [[PAL[c] for c in line.replace(' ', '')] for line in lines]

# Two 8x9 frames stacked vertically; each frame tiles horizontally.
BEAM_A = [
    "OOOOOOOO",
    "RRPRRRRR",
    "PPPPPLPP",
    "LWWLLLLL",
    "WWWWWWWW",
    "LLLLLWWL",
    "PLPPPPPP",
    "RRRRRRPR",
    "OOOOOOOO",
]
BEAM_B = [
    "OOOOOOOO",
    "RRRRRRPR",
    "PLPPPPPP",
    "LLLLLWWL",
    "WWWWWWWW",
    "LWWLLLLL",
    "PPPPPLPP",
    "RRPRRRRR",
    "OOOOOOOO",
]

FLARE_A = [
    ".....P.....",
    ".....L.....",
    "...ORLRO...",
    "..ORPWPRO..",
    "..RPLWLPR..",
    "PLLWWWWWLLP",
    "..RPLWLPR..",
    "..ORPWPRO..",
    "...ORLRO...",
    ".....L.....",
    ".....P.....",
]
FLARE_B = [
    "P.........P",
    ".L.......L.",
    "...ORRRO...",
    "..ORPLPRO..",
    "..RPLWLPR..",
    "..RLWWWLR..",
    "..RPLWLPR..",
    "..ORPLPRO..",
    "...ORRRO...",
    ".L.......L.",
    "P.........P",
]
TIP_A = [
    "...........",
    "...........",
    ".....P.....",
    "....RLR....",
    "...RLWLR...",
    "..PLWWWLP..",
    "...RLWLR...",
    "....RLR....",
    ".....P.....",
    "...........",
    "...........",
]
TIP_B = [
    "...........",
    "...P...P...",
    ".....L.....",
    "....RLR....",
    "...RLWLR...",
    "..LLWWWLL..",
    "...RLWLR...",
    "....RLR....",
    ".....L.....",
    "...P...P...",
    "...........",
]
AIM = ["PRRR.."]

def build(out_dir):
    beam = grid(BEAM_A) + grid(BEAM_B)
    write_png(os.path.join(out_dir, "computah_laser_beam.png"), 8, 18, beam)
    fx_frames = [grid(FLARE_A), grid(FLARE_B), grid(TIP_A), grid(TIP_B)]
    fx = [sum((f[y] for f in fx_frames), []) for y in range(11)]
    write_png(os.path.join(out_dir, "computah_laser_fx.png"), 44, 11, fx)
    write_png(os.path.join(out_dir, "computah_laser_aim.png"), 6, 1, grid(AIM))
    return beam, fx_frames

if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    build(out_dir)
