"""Minimal pure-Python PNG read/write (8-bit, non-interlaced) + helpers."""
import zlib, struct

def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not png'
    pos = 8
    idat = b''
    plte = None
    trns = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        body = data[pos+8:pos+8+ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct, cm, fm, il = struct.unpack('>IIBBBBB', body)
        elif typ == b'PLTE':
            plte = [tuple(body[i:i+3]) for i in range(0, len(body), 3)]
        elif typ == b'tRNS':
            trns = body
        elif typ == b'IDAT':
            idat += body
        elif typ == b'IEND':
            break
    assert il == 0, 'interlaced unsupported'
    raw = zlib.decompress(idat)
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    if bd == 8:
        bpp = chans
        stride = w * chans
    else:
        assert ct in (3, 0), 'low bit depth only for palette/gray'
        bpp = 1
        stride = (w * bd + 7) // 8
    rows = []
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i+stride]); i += stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x-bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x-bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append(line)
        prev = line
    px = []
    for y in range(h):
        line = rows[y]
        row = []
        for x in range(w):
            if bd != 8:
                byte = line[(x*bd)//8]
                shift = 8 - bd - ((x*bd) % 8)
                v = (byte >> shift) & ((1 << bd) - 1)
                if ct == 3:
                    r, g, b = plte[v]
                    a = trns[v] if trns and v < len(trns) else 255
                    row.append((r, g, b, a))
                else:
                    g = v * 255 // ((1 << bd) - 1)
                    row.append((g, g, g, 255))
                continue
            o = x * chans
            if ct == 6:
                row.append(tuple(line[o:o+4]))
            elif ct == 2:
                r, g, b = line[o:o+3]
                a = 255
                if trns and len(trns) == 6:
                    tr = struct.unpack('>HHH', trns)
                    if (r, g, b) == tr: a = 0
                row.append((r, g, b, a))
            elif ct == 3:
                v = line[o]
                r, g, b = plte[v]
                a = trns[v] if trns and v < len(trns) else 255
                row.append((r, g, b, a))
            elif ct == 0:
                g = line[o]; row.append((g, g, g, 255))
            elif ct == 4:
                g, a = line[o:o+2]; row.append((g, g, g, a))
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

def crop(px, x0, y0, w, h):
    return [row[x0:x0+w] for row in px[y0:y0+h]]

def scale(px, s, bg=None):
    out = []
    for row in px:
        r = []
        for p in row:
            if bg is not None and p[3] == 0:
                p = bg
            r.extend([p] * s)
        for _ in range(s):
            out.append(list(r))
    return out

def blank(w, h, c=(0, 0, 0, 0)):
    return [[c] * w for _ in range(h)]

def paste(dst, src, ox, oy, bg_only_alpha=True):
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if 0 <= oy+y < len(dst) and 0 <= ox+x < len(dst[0]):
                if p[3] > 0:
                    dst[oy+y][ox+x] = p
