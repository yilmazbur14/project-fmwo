"""6x close-up sheet: every new entrance design beside the original liam.png and bixby.png, with section labels.
Built as a texel canvas, then streamed to PNG at 6x (row by row) to keep memory low."""
import os
import struct
import sys
import zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Canvas, from_png, rect
from liamkit import LIAM_PNG, BIX_PNG
import throne
import carriers
import liam_seated
import slap
import swallow
import transform
import compose

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'liam_entrance', 'closeup_6x_entrance_designs.png'))
S = 6
BG = (34, 36, 44, 255)
PANEL = (58, 64, 74, 255)
FLOOR = (136, 180, 99, 255)
INK = (238, 232, 214, 255)
ACCENT = (251, 242, 54, 255)

F35 = {
    'A': "010101111101101", 'B': "110101110101110", 'C': "011100100100011", 'D': "110101101101110", 'E': "111100110100111",
    'F': "111100110100100", 'G': "011100101101011", 'H': "101101111101101", 'I': "111010010010111", 'J': "001001001101010",
    'K': "101101110101101", 'L': "100100100100111", 'M': "101111111101101", 'N': "110101101101101", 'O': "010101101101010",
    'P': "110101110100100", 'Q': "010101101110011", 'R': "110101110101101", 'S': "011100010001110", 'T': "111010010010010",
    'U': "101101101101111", 'V': "101101101101010", 'W': "101101111111101", 'X': "101101010101101", 'Y': "101101010010010",
    'Z': "111001010100111", '0': "111101101101111", '1': "010110010010111", '2': "110001010100111", '3': "110001010001110",
    '4': "101101111001001", '5': "111100110001110", '6': "011100111101111", '7': "111001010010010", '8': "111101111101111",
    '9': "111101111001110", ' ': "000000000000000", '-': "000000111000000", '+': "000010111010000", '(': "010100100100010",
    ')': "010001001001010", ':': "000010000010000", '.': "000000000000010", '/': "001001010100100", 'X2': "",
    ',': "000000000010100", '@': "010101111100011", '!': "010010010000010", '=': "000111000111000",
}


def text(cv, s, x, y, col):
    cx = x
    for ch in s.upper():
        g = F35[ch]
        for j in range(5):
            for i in range(3):
                if g[j * 3 + i] == '1':
                    cv.put(cx + i, y + j, col)
        cx += 4
    return cx - x


def panel(cv, x, y, w, h, col=PANEL):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            cv.put(xx, yy, col)


def place(cv, sprite, x, y, bg=PANEL):
    panel(cv, x, y, sprite.w, sprite.h, bg)
    cv.blit(sprite, x, y)
    return sprite.w


def build():
    W, H = 880, 808
    cv = Canvas(W, H)
    panel(cv, 0, 0, W, H, BG)
    M = 8
    # ---- section 1: originals, seated, carriers, walk
    y = M
    x = M
    text(cv, 'ORIGINAL LIAM + BIXBY (APPROVED)', x, y, ACCENT)
    place(cv, from_png(LIAM_PNG), x, y + 8)
    place(cv, from_png(BIX_PNG), x + 68, y + 8)
    x += 132 + 10
    text(cv, 'LIAM SEATED 88X64', x, y, INK)
    place(cv, liam_seated.build(), x, y + 8)
    x += 88 + 10
    text(cv, 'CARRIERS 0-3 32X32', x, y, INK)
    for i, c in enumerate(carriers.build_all()):
        place(cv, c, x + i * 36, y + 8 + 32)
    x += 140 + 10
    text(cv, 'CARRIER WALK 0-3', x, y, INK)
    for i, c in enumerate(carriers.c1_walk()):
        place(cv, c, x + i * 36, y + 8 + 32)
    # ---- section 2: palanquin + assembled procession
    y = M + 8 + 64 + 12
    x = M
    f0, f1 = throne.build()
    text(cv, 'THRONE 200X128: F0 + REAR POLE F1', x, y, INK)
    both = Canvas(throne.FW, throne.FH)
    both.blit(f1)
    both.blit(f0)
    place(cv, both, x, y + 8 + 18)
    x += throne.FW + 12
    text(cv, 'PROCESSION ASSEMBLED', x, y, INK)
    proc = Canvas(216, 146)
    frames = dict(zip(['c1', 'c2', 'c3', 'c4'], carriers.build_all()))
    compose.procession(proc, 12, 2, carrier_frames=frames)
    place(cv, proc, x, y + 8, FLOOR)
    # ---- section 3: slap keys + fed up
    y += 8 + 146 + 12
    x = M
    keys, fed = slap.build()
    text(cv, 'SLAP KEYS 0 WIND-UP  1 SMACK  2 HE LIKES IT   +   FED UP', x, y, INK)
    for i, k in enumerate(keys + [fed]):
        place(cv, k, x + i * 132 + (8 if i == 3 else 0), y + 8)
    # ---- section 4: swallow keys
    y += 8 + 96 + 12
    text(cv, 'SWALLOW KEYS 0 LUNGE  1 CHOMP  2 GULP', x, y, INK)
    for i, k in enumerate(swallow.build()):
        place(cv, k, x + i * 132, y + 8)
    # ---- section 5 (right column): transform keys stacked
    x = M + 536 + 16
    y = M
    text(cv, 'TRANSFORM KEYS 320X256', x, y, INK)
    text(cv, '0 GLOW  1 SWELL  2 FLASH', x, y + 7, INK)
    for i, k in enumerate(transform.build()):
        place(cv, k, x, y + 16 + i * 262, (40, 44, 52, 255))
    return cv


def write_scaled_png(cv, path, s):
    w, h = cv.w * s, cv.h * s

    def chunk(t, b):
        c = struct.pack('>I', len(b)) + t + b
        return c + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    comp = zlib.compressobj(9)
    idat = bytearray()
    for y in range(cv.h):
        row = bytearray([0])
        for p in cv.px[y]:
            row.extend(bytes(p if p is not None else (0, 0, 0, 0)) * s)
        for _ in range(s):
            idat.extend(comp.compress(bytes(row)))
    idat.extend(comp.flush())
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b'IDAT', bytes(idat)))
        f.write(chunk(b'IEND', b''))
    return w, h


if __name__ == '__main__':
    cv = build()
    print(OUT, write_scaled_png(cv, OUT, S))
    cv.save(os.path.normpath(os.path.join(HERE, '..', 'le_prev', 'closeup_1x.png')))
