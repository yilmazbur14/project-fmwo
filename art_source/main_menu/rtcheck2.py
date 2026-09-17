"""Memory-light PNG comparison: decode both to RGBA bytearrays row by row, compare with transparent pixels
normalised, and report alpha values + non-DB32 colours."""
import sys, zlib, struct
DB32_HEX = ['000000', '222034', '45283c', '663931', '8f563b', 'df7126', 'd9a066', 'eec39a', 'fbf236', '99e550',
            '6abe30', '37946e', '4b692f', '524b24', '323c39', '3f3f74', '306082', '5b6ee1', '639bff', '5fcde4',
            'cbdbfc', 'ffffff', '9badb7', '847e87', '696a6a', '595652', '76428a', 'ac3232', 'd95763', 'd77bba',
            '8f974a', '8a6f30']
DB = set(bytes.fromhex(h) for h in DB32_HEX)


def decode(path):
    data = open(path, 'rb').read()
    pos = 8; idat = []; plte = trns = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]; typ = data[pos + 4:pos + 8]; ch = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', ch)
        elif typ == b'PLTE':
            plte = ch
        elif typ == b'tRNS':
            trns = ch
        elif typ == b'IDAT':
            idat.append(ch)
        elif typ == b'IEND':
            break
    assert bd == 8 and il == 0, (bd, il)
    raw = zlib.decompress(b''.join(idat))
    bpp = {6: 4, 2: 3, 3: 1, 0: 1, 4: 2}[ct]
    stride = w * bpp
    out = bytearray(w * h * 4)
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        ft = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        o = y * w * 4
        if ct == 6:
            out[o:o + w * 4] = line
        elif ct == 2:
            for x in range(w):
                out[o + x * 4:o + x * 4 + 3] = line[x * 3:x * 3 + 3]; out[o + x * 4 + 3] = 255
        elif ct == 3:
            for x in range(w):
                idx = line[x]
                out[o + x * 4:o + x * 4 + 3] = plte[idx * 3:idx * 3 + 3]
                out[o + x * 4 + 3] = trns[idx] if trns is not None and idx < len(trns) else 255
        else:
            raise ValueError('colour type %d' % ct)
        prev = line
    return w, h, out


a, b = sys.argv[1], sys.argv[2]
wa, ha, A = decode(a)
wb, hb, B = decode(b)
assert (wa, ha) == (wb, hb), ((wa, ha), (wb, hb))
diff = 0; alphas = set(); bad = set(); first = None
for k in range(0, len(A), 4):
    pa = A[k:k + 4]; pb = B[k:k + 4]
    alphas.add(pb[3])
    if pb[3] and bytes(pb[:3]) not in DB:
        bad.add(bytes(pb[:3]).hex())
    if pa[3] == 0 and pb[3] == 0:
        continue
    if pa != pb:
        diff += 1
        if first is None:
            first = (k // 4 % wa, k // 4 // wa, bytes(pa).hex(), bytes(pb).hex())
print('%s vs %s: %dx%d, %d differing pixels, alpha values %s, non-DB32 %s, first diff %s' % (
    a.split('/')[-1], b.split('/')[-1], wa, ha, diff, sorted(alphas), sorted(bad)[:5], first))
sys.exit(1 if (diff or bad or (alphas - {0, 255})) else 0)
