from mock import *
def slab_shoulder():
    cv = Canvas(); body(cv, arms='R')
    b0=(24,40); tip=(93,4)
    d=(tip[0]-b0[0],tip[1]-b0[1]); L=math.hypot(*d); u=(d[0]/L,d[1]/L); p=(-u[1],u[0]); hw=9.5
    P=lambda c,a,b:(c[0]+u[0]*a+p[0]*b, c[1]+u[1]*a+p[1]*b)
    flat(cv, poly([P(b0,0,hw),P(b0,0,-hw),P(b0,L-4,-hw),P(b0,L,-hw+6),P(b0,L-8,hw)]),'K')
    head(cv)
    flat(cv, poly([(9,50),(21,50),(20,60),(10,62)]),'K')
    flat(cv, poly([(9,58),(19,57),(22,46),(14,44)]),'W')
    g1=P(b0,-20,0)
    flat(cv, poly([P(b0,-2,2.2),P(b0,-2,-2.2),P(b0,-20,-2.2),P(b0,-20,2.2)]),'m')
    flat(cv, poly([P(b0,0,12),P(b0,0,-12),P(b0,-4,-12),P(b0,-4,12)]),'K')
    flat(cv, ell(g1[0],g1[1],3,3),'K')
    flat(cv, ell(P(b0,-9,0)[0],P(b0,-9,0)[1],5.5,5),'W')
    return cv
def slab_planted():
    cv = Canvas(); body(cv, arms='')
    flat(cv, mirror(poly([(70,48),(82,46),(89,58),(86,66),(80,62)])),'K')
    flat(cv, mirror(poly([(80,60),(88,60),(84,70),(76,72),(73,67)])),'W')
    flat(cv, mirror(ell(73,69,5,5)),'W')
    head(cv)
    flat(cv, poly([(76,40),(94,40),(94,88),(85,96),(76,88)]),'K')
    flat(cv, poly([(71,35),(96,35),(96,41),(71,41)]),'K')
    flat(cv, poly([(82.5,14),(87.5,14),(87.5,35),(82.5,35)]),'m')
    flat(cv, ell(85,12,4,3.5),'K')
    flat(cv, poly([(72,50),(84,50),(86,60),(76,62)]),'K')
    flat(cv, poly([(76,58),(86,58),(89,30),(80,32)]),'W')
    flat(cv, ell(85,26,5.5,5),'W')
    return cv
mocks=[slab_shoulder(), slab_planted()]
S=4; pad=10
out=blank(pad+(96*S+pad)*len(mocks),96*S+2*pad,FL)
for i,m in enumerate(mocks): paste(out, scale(m.rgba(),S), pad+i*(96*S+pad), pad)
write_png('mock_slab.png',len(out[0]),len(out),out)
