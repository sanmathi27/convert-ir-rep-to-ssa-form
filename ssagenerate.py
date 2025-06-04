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

# gen dom tree first
from conversion import *

N = 0

# dfs to find DFS numbers for each node
def DFS(p, n, depfnums, vertex, parent, pre):
    global N
    pre[n] = pre[n] | {p}   # add parent as predecessor
    if depfnums[n] == 0:
        depfnums[n] = N # nodes -> DFS numbers
        vertex[N] = n # DFS numbers -> nodes
        parent[n] = p #node -> parent
        N += 1
        for w in n.ch:
            DFS(n, w, depfnums, vertex, parent, pre)

def ancsoflowsemi(v, ancs, depfnums, semi):
    u = v
    while ancs[v] is not None:
        if depfnums[semi[v]] < depfnums[semi[u]]:
            u = v
        v = ancs[v]
    return u

def dominators(r):
    global N
    store = {}
    depfnums = {}
    semi = {}
    ancs = {}
    immdom = {}
    samedom = {}
    vertex = {}
    parent = {}
    global pre
    pre = {}

    store[None] = []

    for block in bl:
        store[block]   = set()
        depfnums[block] = 0
        semi[block]    = block
        ancs[block]    = None
        immdom[block]  = None
        samedom[block] = None
        pre[block]     = set()

    DFS(None, r, depfnums, vertex, parent, pre)  # first find DFS numbers

    for i in range(N - 1, -1, -1):
        n = vertex[i]
        p = parent[n]
        s = p
        for v in pre[n]:
            if v is None:
                continue
            if depfnums[v] <= depfnums[n]:
                sd = v
            else:
                sd = semi[ancsoflowsemi(v, ancs, depfnums, semi)]
            if sd is not None and s is not None:
                if depfnums[sd] < depfnums[s]:
                    s = sd
        if s is None:
            s = n
        semi[n] = s
        store[s].add(n)
        ancs[n] = p

        for v in store[p]:
            y = ancsoflowsemi(v, ancs, depfnums, semi)
            if semi[y] == semi[v]:
                immdom[v] = p
            else:
                samedom[v] = y
        store[p] = set()

    for i in range(1, N):
        n = vertex[i]
        if samedom[n] is not None:
            immdom[n] = immdom[samedom[n]]
    return immdom


def returnVar(s):
    # Remove any label prefix like "L1:"
    s = re.sub(r'^\s*\w+:\s*', '', s)

    # Truncate at 'goto'
    if 'goto ' in s:
        s = s[:s.find('goto ')]

    var_list = []
    for k in re.findall(r'\b\w+\b', s):
        if k == 'if' or k.isnumeric() or k == '$':
            continue
        var_list.append(k)
    return var_list


# find last occurence of substr in str
def findvars(string, substr, n):
    parts = string.split(substr, n + 1)
    if len(parts) <= n + 1:
        return -1
    return len(string) - len(parts[-1]) - len(substr)

# return last element of list
def last(x):
    return x[-1]

# initialize lists and call renaming
def process():
    cnt = {}
    lisst = {}
    for a in var:
        cnt[a] = 0
        lisst[a] = [0]
    rename(start, lisst, cnt)

replaced_vars = set()

def rename(n, lisst, cnt):
    o = copy.deepcopy(n.instr)
    for k in range(len(n.instr)):
        s = ' ' + n.instr[k] + ' '
        n.instr[k] = s
        vars_here = returnVar(s)
        temp = vars_here

        if '$' not in s:
            if 'if' not in s and len(vars_here) > 0:
                temp = vars_here[1:]  # exclude the ‘if’-condition variable

            # rename using the variable counting
            for x in temp:
                i = last(lisst[x])
                # safe replace: only whole-word matches
                n.instr[k] = re.sub(rf'\b{x}\b', f'{x}_{i}', n.instr[k])
                s = n.instr[k]

        # increment variable count (for definitions)
        if (len(vars_here) > 0 and 'if' not in s and 'goto' not in s 
            and vars_here[0] in cnt):
            v0 = vars_here[0]
            cnt[v0] += 1
            i = cnt[v0]
            lisst[v0].append(i)
            # replace the first occurrence of v0
            n.instr[k] = re.sub(rf'\b{v0}\b', f'{v0}_{i}', n.instr[k], count=1)
            n.instr[k] = n.instr[k].replace(f'\t{v0} ', f'\t{v0}_{i} ', 1)

    # rename inside each phi‐node of children
    for y in n.ch:
        # j = index of n among y’s predecessors
        j = pre[y].index(n)
        for k in range(len(y.instr)):
            line = y.instr[k]
            if '$' in line:
                # a is the phi‐variable (e.g. ‘x’ in “x = $( x , x )”)
                a = returnVar(line)[0]
                if '_' in a:
                    a = a[:a.find('_')]
                a = a.strip()
                ind = findvars(line, a, j + 1)
                if ind != -1 and a in allVar:
                    # replace the j-th occurrence of ‘a’ with its current version
                    version = last(lisst[a])
                    y.instr[k] = line[:ind] + f'{a}_{version}' + line[ind+len(a):]

    # Recursively rename in the dominator‐tree children
    for x in n.dom:
        if x == n:
            continue
        rename(x, lisst, cnt)

def insertPhi(defi, DF, phi, pre):
    for n in bl:
        for a in n.oriv:
            if ':' in a:  # Skippedd label-like variables
                continue
            if a not in defi:
                defi[a] = set()
            defi[a].add(n)

    for a in var:
        if ':' in a:  # Skip labels
            continue
        phi[a] = set()
        w = defi.get(a, set()).copy()
        while w:
            n_block = w.pop()
            for Y in DF[n_block]:
                if Y not in phi[a]:
                    line = a + ' = $( '
                    for _ in range(len(pre[Y])):
                        line += a + ' , '
                    line = line[:-2] + ' )'
                    Y.instr.insert(0, line)
                    phi[a].add(Y)
                    if a not in Y.oriv:
                        w.add(Y)


def computeDF(n, DF):
    S = set()
    for y in n.ch:
        if immdom[y] != n:
            S.add(y)

    for c in n.dom:
        if c == n:
            continue
        computeDF(c, DF)
        for w in DF[c]:
            if w not in n.dom:
                S.add(w)
    DF[n] = S


# 1) Build the dominator tree
immdom = dominators(start)
for i in immdom:
    if immdom[i] is not None:
        immdom[i].dom.add(i)

# 2) Compute dominance frontiers
DF = {}
computeDF(start, DF)

# 3) Convert each set of predecessors from `pre[...]` into a list
for i in pre:
    pre[i] = list(pre[i])

# 4) Insert phi‐nodes
phi = {}
defi = {}
insertPhi(defi, DF, phi, pre)

# 5) Rename variables to finalize SSA
allVar = var
process()

# 6) Print out the final SSA form
print('\n\nSSA\n\n')
for blk in bl:
    blk.disp()

    
