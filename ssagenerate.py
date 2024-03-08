
import copy
import re

#gen dom tree first
from conversion import *

N=0

def ancsoflowsemi(v,ancs,depfnums,semi): #find ancestor using semi number (dominance frontier)
    u=v
    while ancs[v]!=None:
        if depfnums[semi[v]]<depfnums[semi[u]]:
            u=v
        v=ancs[v]
    return u

def DFS(p,n,depfnums,vertex,parent,pre):
    global N
    pre[n]=pre[n] | {p}
    if depfnums[n]==0:
        depfnums[n]=N
        vertex[N]=n
        parent[n]=p
        N=N + 1
        for w in n.ch:
            DFS(n,w,depfnums,vertex,parent,pre)

def dominators(r):
    global N
    store={}
    depfnums={}
    semi={}
    ancs={}
    immdom={}
    samedom={}
    vertex={}
    parent={}
    global pre
    pre={}
    store[None]=[]
    for i in b.keys():
        store[b[i]]=set()
        depfnums[b[i]]=0
        semi[b[i]]=b[i]
        ancs[b[i]]=None
        immdom[b[i]]=None
        samedom[b[i]]=None
        pre[b[i]]=set()

    DFS(None,r,depfnums,vertex,parent,pre)#first find  depth first nums

    for i in range(N-1,-1,-1): #go in reverse
        n=vertex[i]
        p=parent[n]
        s=p
        for v in pre[n]: #semi-doms
            if v==None:
                continue
            if depfnums[v]<=depfnums[n]:
                sd=v
            else:
                sd=semi[ancsoflowsemi(v,ancs,depfnums,semi)]
            
            if sd!=None and s!=None:
                if depfnums[sd]<depfnums[s]:
                    s=sd
        if s==None:
            s=n
        semi[n]=s
        store[s] |= {n}
        ancs[n]=p
        
        for v in store[p]:
            y=ancsoflowsemi(v,ancs,depfnums,semi)
            if semi[y]==semi[v]:
                immdom[v]=p
            else:
                samedom[v]=y

            store[p]=set()
        
    for i in range(1,N):
        n=vertex[i]
        if samedom[n]!=None:
            immdom[n]=immdom[samedom[n]] #cuz imm dom of n same as imm dom of same dominator
    return immdom

immdom=dominators(start)
for i in immdom.keys():
    if immdom[i]!=None:
        immdom[i].dom |= {i}




def findvars(str, substr, n):
    parts= str.split(substr, n+1)
    if len(parts)<=n+1:
        return -1
    return len(str)-len(parts[-1])-len(substr)

def last(x):
    return x[len(x)-1]

def returnVar(s):
    var=[]
    if s.find('goto ')!=-1:
        s=s[:s.find('goto ')]
    for k in re.findall('\w\w*:?',s):
        if k=='if' or ':' in k or k.isnumeric() or k=='$':
            continue
        var.append(k)
    return var

def process():
    cnt={}
    lisst={}
    for a in var:
        cnt[a]=0
        lisst[a]=[]
        lisst[a].append(0)
    rename(start,lisst,cnt)


def rename(n,lisst,cnt):
    o=copy.deepcopy(n.instr)
    for k in range(len(n.instr)):
        s=' '+n.instr[k]+' ' #dont remove pls
        n.instr[k]=s
        var=returnVar(s)
        tempVar=var
        if '$' not in s:
            if 'if' not in s and len(var)>0:
                tempVar=var[1:]
            for x in tempVar:
                if x not in lisst.keys():
                    continue
                i=last(lisst[x])
                n.instr[k]=s.replace(' '+x+' ',' '+x+'_'+str(i)+' ') #generated
                n.instr[k]=n.instr[k].replace('-'+x+' ',' '+x+'_'+str(i)+' ')
                

        if len(var)>0 and 'if' not in s and 'goto' not in s and var[0] in cnt.keys():
            cnt[var[0]]=cnt[var[0]]+1
            i=cnt[var[0]]
            lisst[var[0]].append(i)
            n.instr[k]=n.instr[k].replace(' '+var[0]+' ',' '+var[0]+'_'+str(i)+' ',1)
            n.instr[k]=n.instr[k].replace('\t'+var[0]+' ','\t'+var[0]+'_'+str(i)+' ',1)


    for y in n.ch:
        j=pre[y].index(n)
        for k in range(len(y.instr)):
            line=y.instr[k]
            if '$' in line:
                a=returnVar(line)
                a=a[0]
                if a.find('_')!=-1:
                    a=a[:a.find('_')]
                a=a.strip()
                ind=findvars(line,a,j+1)
                if ind!=-1 and a in allVar:
                    y.instr[k]=line[:ind]+a+'_'+str(last(lisst[a]))+line[ind+len(a):]#generated
    
    for x in n.dom:
        if x==n:
            continue
        rename(x,lisst,cnt)


def insertPhi(defi,DF,phi,pre):
    for n in bl:
        for a in n.oriv:
            if a not in defi.keys():
                defi[a]=set()
            else:
                defi[a] |= {n}  #find where 'a' is defined
        
        
    
    for a in var:
        phi[a] = set()
        w = defi[a].copy()
        while w:
            n = w.pop()
            for Y in DF[n]:
                if Y not in phi[a]:
                    line = a + ' = $( '
                    for numPred in range(len(pre[Y])):
                        line += a + ' , '
                    line = line[:-2] + ')'
                    Y.instr.insert(0, line)
                    phi[a].add(Y)
                    if a not in Y.oriv:
                        w.add(Y)


def computeDF(n,DF):
    S=set()
    for y in n.ch:
        if immdom[y]!=n:
            S |= {y}

    for c in n.dom:
        if c==n:
            continue
        computeDF(c,DF)
        for w in DF[c]:
            if w not in n.dom:
                S=S.union({w})
    DF[n]=S


DF={}

computeDF(start,DF)
phi={}
defi={}


for i in pre.keys():
    pre[i]=list(pre[i])

insertPhi(defi,DF,phi,pre)

allVar=var
    
process()

print('\n\nSSA\n\n')
for i in bl:
    i.disp()
    