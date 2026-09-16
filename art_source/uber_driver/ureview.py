import sys, os, zlib, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from png_read import read_png


def strip(paths_frames, scale, bg, out):
    """paths_frames: list of 64x64 RGBA grids."""
    n = len(paths_frames)
    raw = bytearray()
    for y in range(64):
        line = bytearray()
        for g in paths_frames:
            for x in range(64):
                px = g[y][x]
                px = bg if px[3] == 0 else px
                line += bytes((px[0], px[1], px[2], 255)) * scale
        for _ in range(scale):
            raw += b'\x00' + line

    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 64 * n * scale, 64 * scale, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    open(out, 'wb').write(png)


def frames_of(path):
    w, h, px = read_png(path)
    return [[[px[y][x0 + x] for x in range(64)] for y in range(64)] for x0 in range(0, w, 64)]


if __name__ == '__main__':
    sheet, mason, out, scale = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    fr = frames_of(sheet)
    if mason != '-':
        fr = frames_of(mason)[:1] + fr
    strip(fr, scale, (88, 96, 104, 255), out)
    print('ok', len(fr), 'frames')
