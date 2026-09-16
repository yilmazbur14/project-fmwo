"""Private PNG helpers for the poo FX work (pure Python, RGBA8). Do not share - other
artists use the scratchpad root."""
import struct
import zlib


def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
    pos = 8
    idat = b''
    plte = trns = None
    w = h = bd = ct = il = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct, _cm, _fm, il = struct.unpack('>IIBBBBB', body)
        elif typ == b'PLTE':
            plte = body
        elif typ == b'tRNS':
            trns = body
        elif typ == b'IDAT':
            idat += body
        elif typ == b'IEND':
            break
    assert il == 0, 'interlaced png unsupported'
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    if ct == 3:
        stride = (w * bd + 7) // 8
        bpp = 1
    else:
        assert bd == 8, 'bitdepth %d unsupported' % bd
        stride = w * ch
        bpp = ch
    raw = zlib.decompress(idat)
    rows, prev, i = [], bytearray(stride), 0
    for _y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        rows.append(line)
        prev = line
    px = []
    for line in rows:
        row = []
        for x in range(w):
            if ct == 6:
                row.append(tuple(line[x * 4:x * 4 + 4]))
            elif ct == 2:
                row.append(tuple(line[x * 3:x * 3 + 3]) + (255,))
            elif ct == 0:
                row.append((line[x],) * 3 + (255,))
            elif ct == 4:
                row.append((line[x * 2],) * 3 + (line[x * 2 + 1],))
            else:
                if bd == 8:
                    idx = line[x]
                else:
                    byte = line[(x * bd) // 8]
                    idx = (byte >> (8 - bd - ((x * bd) % 8))) & ((1 << bd) - 1)
                r, g, b = plte[idx * 3:idx * 3 + 3]
                a = trns[idx] if trns and idx < len(trns) else 255
                row.append((r, g, b, a))
        px.append(row)
    return w, h, px


def write_png(path, w, h, px):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(bytes(px[y][x]))

    def chunk(t, b):
        c = struct.pack('>I', len(b)) + t + b
        return c + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)

    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)


def view(w, h, px, k, bg='checker', grid=None, gridcol=(255, 0, 255, 255)):
    """Nearest-neighbour upscale for viewing. bg: 'checker' or an (r,g,b) tuple or a
    background pixel array (same w/h as px, already at 1x). grid=(fw,fh) draws frame
    separators one screen-pixel wide."""
    out = []
    for Y in range(h * k):
        y = Y // k
        row = []
        for X in range(w * k):
            x = X // k
            p = px[y][x]
            if bg == 'checker':
                c = 150 if ((x + y) % 2 == 0) else 125
                base = (c, c, c + 10)
            elif isinstance(bg, list):
                base = bg[y][x][:3]
            else:
                base = bg
            a = p[3] / 255.0
            q = tuple(int(round(p[i] * a + base[i] * (1 - a))) for i in range(3)) + (255,)
            if grid is not None:
                fw, fh = grid
                if (fw and X % (fw * k) == 0 and X > 0) or (fh and Y % (fh * k) == 0 and Y > 0):
                    q = gridcol
            row.append(q)
        out.append(row)
    return w * k, h * k, out


def hexc(s):
    s = s.lstrip('#')
    if len(s) == 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16))
