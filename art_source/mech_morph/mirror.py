import sys
rows=[r.rstrip('\n') for r in open(sys.argv[1]) if r.strip('\n')]
out=[]
for i,r in enumerate(rows):
    if len(r)!=15: print('row',i,'len',len(r))
    out.append(r+r[::-1])
open(sys.argv[2],'w').write('\n'.join(out)+'\n')
