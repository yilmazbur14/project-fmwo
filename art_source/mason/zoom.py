import sys, zlib, struct
from png import read_png

def write_png(path, w, h, px):
    raw = b''
    for y in range(h):
        raw += b'\x00' + bytes(v for x in range(w) for v in px[y][x])
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(raw, 9))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)

def upscale(src, dst, f, checker=True):
    w, h, px = read_png(src)
    W, H = w * f, h * f
    out = []
    for Y in range(H):
        row = []
        for X in range(W):
            p = px[Y // f][X // f]
            if p[3] == 0 and checker:
                # light checkerboard so transparent area is distinguishable from white
                c = 235 if ((X // f) + (Y // f)) % 2 == 0 else 205
                p = (c, c, c, 255)
            row.append(p)
        out.append(row)
    write_png(dst, W, H, out)
    print('wrote', dst, W, 'x', H)

if __name__ == '__main__':
    src = sys.argv[1]; dst = sys.argv[2]; f = int(sys.argv[3])
    checker = (len(sys.argv) < 5 or sys.argv[4] != 'nochecker')
    upscale(src, dst, f, checker)
