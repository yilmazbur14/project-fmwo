"""Pure-python PNG read/write + helpers (no PIL available)."""
import zlib, struct

def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not png'
    pos = 8
    idat = b''
    plte = None
    trns = None
    w = h = bd = ct = il = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        body = data[pos+8:pos+8+ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', body)
        elif typ == b'PLTE':
            plte = [tuple(body[i:i+3]) for i in range(0, len(body), 3)]
        elif typ == b'tRNS':
            trns = body
        elif typ == b'IDAT':
            idat += body
        elif typ == b'IEND':
            break
    assert il == 0, 'interlaced not supported'
    raw = zlib.decompress(idat)
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bpp_bits = chans * bd
    stride = (w * bpp_bits + 7) // 8
    bpp = max(1, bpp_bits // 8)
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
        rows.append(bytes(line))
        prev = line
    px = []
    for y in range(h):
        line = rows[y]
        row = []
        if bd == 8:
            for x in range(w):
                o = x * chans
                if ct == 6:
                    row.append(tuple(line[o:o+4]))
                elif ct == 2:
                    r, g, b = line[o:o+3]
                    a = 255
                    if trns and len(trns) >= 6:
                        tr = struct.unpack('>HHH', trns[:6])
                        if (r, g, b) == tr: a = 0
                    row.append((r, g, b, a))
                elif ct == 0:
                    v = line[o]; row.append((v, v, v, 255))
                elif ct == 4:
                    v, a = line[o:o+2]; row.append((v, v, v, a))
                elif ct == 3:
                    idx = line[o]
                    r, g, b = plte[idx]
                    a = trns[idx] if (trns and idx < len(trns)) else 255
                    row.append((r, g, b, a))
        else:
            assert ct in (3, 0), 'unsupported bit depth combo'
            mask = (1 << bd) - 1
            for x in range(w):
                bit = x * bd
                byte = line[bit // 8]
                shift = 8 - bd - (bit % 8)
                idx = (byte >> shift) & mask
                if ct == 3:
                    r, g, b = plte[idx]
                    a = trns[idx] if (trns and idx < len(trns)) else 255
                    row.append((r, g, b, a))
                else:
                    v = idx * 255 // mask
                    row.append((v, v, v, 255))
        px.append(row)
    return w, h, px

def write_png(path, w, h, px):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(px[y][x])
    def chunk(t, b):
        c = struct.pack('>I', len(b)) + t + b
        return c + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)

def scale(w, h, px, s):
    out = []
    for y in range(h * s):
        sy = y // s
        out.append([px[sy][x // s] for x in range(w * s)])
    return w * s, h * s, out

def crop(w, h, px, x0, y0, cw, ch):
    return cw, ch, [[px[y][x] for x in range(x0, x0 + cw)] for y in range(y0, y0 + ch)]

def blank(w, h, c=(0, 0, 0, 0)):
    return [[c for _ in range(w)] for _ in range(h)]

def paste(dst, src, sw, sh, ox, oy):
    for y in range(sh):
        for x in range(sw):
            p = src[y][x]
            if p[3] == 0:
                continue
            dst[oy + y][ox + x] = p

def checker_bg(w, h, px, cell=8, c1=(200, 200, 200, 255), c2=(170, 170, 170, 255)):
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            p = px[y][x]
            if p[3] == 255:
                row.append(p)
            else:
                bg = c1 if ((x // cell + y // cell) % 2 == 0) else c2
                a = p[3] / 255.0
                row.append(tuple(int(p[i] * a + bg[i] * (1 - a)) for i in range(3)) + (255,))
        out.append(row)
    return out

def grid_overlay(w, h, px, s, every=8, col=(255, 0, 255, 255)):
    """Draw faint grid lines every `every` source pixels on an s-scaled image."""
    out = [list(r) for r in px]
    for y in range(h):
        for x in range(w):
            if (x % (every * s) == 0) or (y % (every * s) == 0):
                p = out[y][x]
                out[y][x] = tuple((p[i] * 2 + col[i]) // 3 for i in range(3)) + (255,)
    return out
