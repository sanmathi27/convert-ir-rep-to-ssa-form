#dominance tree generated, cfg converted to ssa
#ancestors are found based on semi-number and dfs done to calculate dominance nums
#phi nodes inserted at join points

# DFS- performs dfs, assigns dfs numbers, constructs the vertex and parent dicts, records predecessors
# ancsoflowsemi - determines semi numbers in the dominance frontier
# dominators - compute immediate dominator for each node, even semi-dominators
# findvars - recent occurence of a specific variable
# process - initializations for renaming
# rename - rename variables, update variable counts
# insertphi - inserting phi funcs at join pts based on dominance frontier
# computeDF - calculates dominance frontier for each node in cfg using DFS

import copy
import re

#gen dom tree first
from conversion import *

N=0

def DFS(p,n,depfnums,vertex,parent,pre): #depth first search to compute depth first numbering
    global N
    pre[n]=pre[n] | {p} # add parent as predecessor
    if depfnums[n]==0:
        depfnums[n]=N # node -> depfsnums
        vertex[N]=n # depfnums -> current node
        parent[n]=p
        N=N + 1
        for w in n.ch:
            DFS(n,w,depfnums,vertex,parent,pre)

def ancsoflowsemi(v,ancs,depfnums,semi): #find ancestor using semi number (dominance frontier)
    u=v
    while ancs[v]!=None:
        if depfnums[semi[v]]<depfnums[semi[u]]: #depth first numbering
            u=v
        v=ancs[v]
    return u


#find immediate dominator for each node
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
        
        #update immediate dominators n same dominators for each node
        for v in store[p]:
            y=ancsoflowsemi(v,ancs,depfnums,semi)
            if semi[y]==semi[v]:
                immdom[v]=p
            else:
                samedom[v]=y

            store[p]=set()
    #update imm dom based on same dominators
    for i in range(1,N):
        n=vertex[i]
        if samedom[n]!=None:
            immdom[n]=immdom[samedom[n]] #cuz imm dom of n same as imm dom of same dominator
    return immdom

#find out node set as imm dominator
immdom=dominators(start)
for i in immdom.keys():
    if immdom[i]!=None:
        immdom[i].dom |= {i}



#last occurence of substr in str
def findvars(str, substr, n):
    parts= str.split(substr, n+1)
    #check if substr occurred less than n times
    if len(parts)<=n+1:
        return -1
    return len(str)-len(parts[-1])-len(substr)

#return last element of list
def last(x):
    return x[len(x)-1]

#extract variables from string
def returnVar(s):
    var=[]
    if s.find('goto ')!=-1:
        s=s[:s.find('goto ')]
    #extract using regular exp
    for k in re.findall(r'\b\w+\b', s):
        #skip keywords
        if k=='if' or ':' in k or k.isnumeric() or k=='$':
            continue
        var.append(k)
    return var

#initialize lists and call renaming
def process():
    cnt={}
    lisst={}
    for a in var:
        cnt[a]=0
        lisst[a]=[]
        lisst[a].append(0)
    rename(start,lisst,cnt)

replaced_vars = set()
def rename(n,lisst,cnt):
    o=copy.deepcopy(n.instr)
    for k in range(len(n.instr)):
        s=' '+n.instr[k]+' ' #dont remove pls
        n.instr[k]=s
        var=returnVar(s)
        temp=var
        if '$' not in s:
            if 'if' not in s and len(var)>0:
                temp=var[1:] #exclude 'if'
            #rename using the variable counting
            for x in temp:
                i=last(lisst[x])
                print(i)
                n.instr[k] = s.replace(f'{x} ', f'{x}_{i} ').replace(f'^{x} ', f'^{x}_{i} ') 
                s=n.instr[k] # Generate replacement
                n.instr[k]=n.instr[k].replace('-'+x+' ',' '+x+'_'+str(i)+' ')
                s=n.instr[k]
        #incrementing variable counts
        if len(var)>0 and 'if' not in s and 'goto' not in s and var[0] in cnt.keys():
            cnt[var[0]]=cnt[var[0]]+1
            i=cnt[var[0]]
            lisst[var[0]].append(i)
            n.instr[k] = n.instr[k].replace(f' {var[0]} ', f' {var[0]}_{i} ', 1)
            n.instr[k] = n.instr[k].replace(f'\t{var[0]} ', f'\t{var[0]}_{i} ', 1) #for some reason the ones with tab wont get replaced if not for this line

    #for the variables inside phi

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
    #for renaming in dominator tree
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
        
        
    #insert phi funcs
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

#compute dominance frontiers
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

#stores dom frontiers
DF={}

computeDF(start,DF)
phi={}
defi={} #store defined variables


for i in pre.keys():
    pre[i]=list(pre[i])

insertPhi(defi,DF,phi,pre)

allVar=var
    
process()

print('\n\nSSA\n\n')
for i in bl:
    i.disp()
    