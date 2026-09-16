import struct, zlib, sys

def read_png(path):
    d = open(path,'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat = b''
    plte = None
    trns = None
    w=h=bd=ct=0
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos+4])[0]
        typ = d[pos+4:pos+8]
        data = d[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w,h,bd,ct,_,_,inter = struct.unpack('>IIBBBBB', data)
            assert bd == 8, 'bitdepth %d' % bd
            assert inter == 0, 'interlaced'
        elif typ == b'PLTE':
            plte = data
        elif typ == b'tRNS':
            trns = data
        elif typ == b'IDAT':
            idat += data
        elif typ == b'IEND':
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    nch = {0:1, 2:3, 3:1, 4:2, 6:4}[ct]
    stride = w * nch
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if f == 1:
            for i in range(nch, stride): line[i] = (line[i] + line[i-nch]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i-nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i-nch] if i >= nch else 0
                b = prev[i]
                c = prev[i-nch] if i >= nch else 0
                pa = abs(b-c); pb = abs(a-c); pc = abs(a+b-2*c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out += line
        prev = line
    # to RGBA
    px = []
    for y in range(h):
        row = []
        for x in range(w):
            i = (y*w+x)*nch
            if ct == 6: r,g,b,a = out[i],out[i+1],out[i+2],out[i+3]
            elif ct == 2: r,g,b,a = out[i],out[i+1],out[i+2],255
            elif ct == 3:
                idx = out[i]; r,g,b = plte[idx*3],plte[idx*3+1],plte[idx*3+2]
                a = trns[idx] if trns and idx < len(trns) else 255
            elif ct == 0: r=g=b=out[i]; a=255
            else: r=g=b=out[i]; a=out[i+1]
            row.append((r,g,b,a))
        px.append(row)
    return w,h,px

def hx(c): return '#%02X%02X%02X' % c[:3]

if __name__ == '__main__':
    w,h,px = read_png(sys.argv[1])
    from collections import Counter
    c = Counter()
    for row in px:
        for p in row:
            if p[3] > 0: c[p[:3]] += 1
    print(w, 'x', h, '  opaque colors:', len(c))
    for col, n in c.most_common(40):
        print('  %s  %5d' % (hx(col), n))
