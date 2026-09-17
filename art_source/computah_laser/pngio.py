import zlib, struct

def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat = b''
    palette = None
    trns = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        body = data[pos+8:pos+8+ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct, comp, filt, inter = struct.unpack('>IIBBBBB', body)
        elif typ == b'PLTE':
            palette = [tuple(body[i:i+3]) for i in range(0, len(body), 3)]
        elif typ == b'tRNS':
            trns = body
        elif typ == b'IDAT':
            idat += body
    assert bd == 8 and inter == 0, (bd, inter)
    ch = {6: 4, 2: 3, 0: 1, 4: 2, 3: 1}[ct]
    raw = zlib.decompress(idat)
    stride = w * ch
    out = []
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i+stride]); i += stride
        for x in range(stride):
            a = line[x-ch] if x >= ch else 0
            b = prev[x]
            c = prev[x-ch] if x >= ch else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        prev = line
        row = []
        for x in range(w):
            px = line[x*ch:(x+1)*ch]
            if ct == 6: row.append(tuple(px))
            elif ct == 2: row.append((px[0], px[1], px[2], 255))
            elif ct == 0: row.append((px[0], px[0], px[0], 255))
            elif ct == 4: row.append((px[0], px[0], px[0], px[1]))
            elif ct == 3:
                r, g, b = palette[px[0]]
                al = trns[px[0]] if trns and px[0] < len(trns) else 255
                row.append((r, g, b, al))
        out.append(row)
    return w, h, out

def write_png(path, w, h, rows):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(rows[y][x])
    def chunk(t, b):
        return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)

def upscale(w, h, rows, s, bg=None):
    out = []
    for y in range(h):
        r = []
        for x in range(w):
            p = rows[y][x]
            if bg is not None and p[3] == 0:
                p = bg
            r.extend([p] * s)
        for _ in range(s):
            out.append(list(r))
    return w * s, h * s, out
