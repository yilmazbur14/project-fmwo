import sys, struct
def decode(path):
    d=open(path,'rb').read(); assert d[:6]==b'GIF89a'
    w,h,flags,bg,asp=struct.unpack('<HHBBB',d[6:13]); pos=13
    gct=[]
    if flags&0x80:
        n=2<<(flags&7); gct=[tuple(d[pos+3*i:pos+3*i+3]) for i in range(n)]; pos+=3*n
    frames=[];durs=[]
    while True:
        b=d[pos]; pos+=1
        if b==0x3b: break
        if b==0x21:
            label=d[pos]; pos+=1
            if label==0xf9: durs.append(struct.unpack('<H',d[pos+2:pos+4])[0]*10)
            while True:
                n=d[pos]; pos+=1
                if n==0: break
                pos+=n
        elif b==0x2c:
            x,y,fw,fh,fl=struct.unpack('<HHHHB',d[pos:pos+9]); pos+=9
            mcs=d[pos]; pos+=1; data=bytearray()
            while True:
                n=d[pos]; pos+=1
                if n==0: break
                data+=d[pos:pos+n]; pos+=n
            clear=1<<mcs; eoi=clear+1
            size=mcs+1; table=[(i,) for i in range(clear)]+[None,None]
            out=[]; bitpos=0; prev=None
            total=len(data)*8
            while bitpos+size<=total:
                code=0
                for i in range(size):
                    code|=((data[(bitpos+i)>>3]>>((bitpos+i)&7))&1)<<i
                bitpos+=size
                if code==clear:
                    size=mcs+1; table=[(i,) for i in range(clear)]+[None,None]; prev=None; continue
                if code==eoi: break
                if prev is None:
                    entry=table[code]; out.extend(entry); prev=entry; continue
                if code<len(table): entry=table[code]
                else: entry=prev+(prev[0],)
                out.extend(entry)
                if len(table)<4096: table.append(prev+(entry[0],))
                if len(table)>=(1<<size) and size<12: size+=1
                prev=entry
            assert len(out)>=fw*fh, (len(out),fw*fh)
            frames.append([[gct[out[yy*fw+xx]] for xx in range(fw)] for yy in range(fh)])
    return w,h,frames,durs
if __name__=='__main__':
    from pngio import *
    w,h,frames,durs=decode(sys.argv[1]); print(w,h,len(frames),durs)
