import math
from pngio import *

FLOOR = (136, 180, 99, 255)
PAL = {
    '.': (0, 0, 0, 0),
    'K': (0, 0, 0, 255),
    'W': (255, 255, 255, 255),
    'L': (197, 205, 209, 255),   # armour/grip light
    '2': (176, 188, 195, 255),   # blade rim light
    '1': (155, 173, 183, 255),   # blade rim
    '5': (147, 143, 149, 255),   # blade speckle
    '4': (132, 126, 135, 255),   # blade body
    '7': (105, 106, 106, 255),   # blade shade
    '3': (86, 87, 87, 255),      # blade dark
    # earth (built off Eric's loincloth browns)
    'd': (102, 57, 49, 255),     # earth dark (Eric dark brown)
    'b': (117, 76, 69, 255),     # earth mid (Eric brown)
    'e': (150, 106, 80, 255),    # earth light
    'f': (184, 146, 110, 255),   # earth highlight / dusty soil
    'g': (60, 36, 32, 255),      # crack/earth deepest
    # turf (arena floor is (136,180,99))
    'H': (172, 210, 128, 255),   # grass highlight
    'G': (136, 180, 99, 255),    # grass = floor colour
    'h': (98, 140, 72, 255),     # grass shadow
}
INV = {v: k for k, v in PAL.items()}

def grid_to_px(lines):
    return [[PAL[c] for c in ln] for ln in lines]

def px_to_grid(px):
    out = []
    for row in px:
        s = ''
        for p in row:
            if p[3] == 0:
                s += '.'
            else:
                s += INV[tuple(p)]
        out.append(s)
    return out

def load_grid(path):
    lines = [ln.rstrip('\n') for ln in open(path) if not ln.startswith(';')]
    lines = [ln for ln in lines if ln]
    return lines

def save_grid(path, lines):
    open(path, 'w').write('\n'.join(lines) + '\n')

def rot90cw(g):
    h = len(g); w = len(g[0])
    return [''.join(g[h - 1 - X][Y] if False else g[w - 1 - X][Y] for X in range(w)) for Y in range(h)]

def strip(frames):
    h = len(frames[0]); out = [''] * h
    for f in frames:
        for y in range(h):
            out[y] += f[y]
    return out

def write_grid_png(path, lines):
    px = grid_to_px(lines)
    write_png(path, len(px[0]), len(px), px)

def view(path, lines, s, bg=FLOOR, sep=None):
    px = grid_to_px(lines)
    z = scale(px, s, bg)
    write_png(path, len(z[0]), len(z), z)
