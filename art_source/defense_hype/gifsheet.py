"""gifsheet.py in.gif out.png [cols] [scale_div] -> contact sheet of every GIF frame (verifies what a GIF holds)"""
import sys, struct
sys.dont_write_bytecode = True
from gifio import _lzw_decode
from pngio import write_png


def read_gif(path):
    b = open(path, 'rb').read()
    assert b[:6] in (b'GIF89a', b'GIF87a')
    w, h, flags, bg, asp = struct.unpack('<HHBBB', b[6:13])
    pos = 13
    gct = []
    if flags & 0x80:
        n = 2 ** ((flags & 7) + 1)
        gct = [tuple(b[pos + 3 * i:pos + 3 * i + 3]) for i in range(n)]
        pos += 3 * n
    frames, delays = [], []
    delay = 0
    while pos < len(b):
        blk = b[pos]
        if blk == 0x21:
            label = b[pos + 1]
            pos += 2
            if label == 0xF9:
                delay = struct.unpack('<H', b[pos + 2:pos + 4])[0]
            while b[pos] != 0:
                pos += b[pos] + 1
            pos += 1
        elif blk == 0x2C:
            x, y, fw, fh, fl = struct.unpack('<HHHHB', b[pos + 1:pos + 10])
            pos += 10
            pal = gct
            if fl & 0x80:
                n = 2 ** ((fl & 7) + 1)
                pal = [tuple(b[pos + 3 * i:pos + 3 * i + 3]) for i in range(n)]
                pos += 3 * n
            mcs = b[pos]
            pos += 1
            data = b''
            while b[pos] != 0:
                data += b[pos + 1:pos + 1 + b[pos]]
                pos += b[pos] + 1
            pos += 1
            idx = _lzw_decode(data, mcs, fw * fh)
            img = [[pal[idx[yy * fw + xx]] for xx in range(fw)] for yy in range(fh)]
            frames.append(img)
            delays.append(delay)
        elif blk == 0x3B:
            break
        else:
            raise ValueError('bad block %x' % blk)
    return w, h, frames, delays


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    div = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    w, h, frames, delays = read_gif(src)
    fw, fh = w // div, h // div
    rows = (len(frames) + cols - 1) // cols
    gap = 6
    W = cols * (fw + gap) + gap
    H = rows * (fh + gap) + gap
    out = [[(255, 0, 255, 255)] * W for _ in range(H)]
    for i, fr in enumerate(frames):
        x0 = gap + (i % cols) * (fw + gap)
        y0 = gap + (i // cols) * (fh + gap)
        for y in range(fh):
            for x in range(fw):
                p = fr[y * div][x * div]
                out[y0 + y][x0 + x] = p + (255,)
    write_png(dst, W, H, out)
    print(src.split('/')[-1], 'frames', len(frames), 'delays(cs)', delays)
