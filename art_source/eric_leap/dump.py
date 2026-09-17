import pickle, sys
frames = pickle.load(open('eric_frames.pkl','rb'))
PAL = {
 (0,0,0):'k', (255,255,255):'w', (197,205,209):'L', (155,173,183):'M', (132,126,135):'s', (86,87,87):'d',
 (102,57,49):'b', (223,113,38):'o', (238,195,154):'t', (217,160,102):'T', (176,188,195):'l', (117,76,69):'B',
 (147,143,149):'g', (236,208,181):'p', (105,106,106):'D', (125,125,125):'G', (81,81,81):'e',
}
def ch(p):
    if p[3]==0: return '.'
    if p[3]<255: return '~'
    return PAL.get(p[:3],'?')
i=int(sys.argv[1]); x0,y0,x1,y1=[int(v) for v in sys.argv[2:6]]
print('    '+''.join(str((x//10)%10) for x in range(x0,x1)))
print('    '+''.join(str(x%10) for x in range(x0,x1)))
for y in range(y0,y1):
    print('%3d '%y+''.join(ch(frames[i][y][x]) for x in range(x0,x1)))
