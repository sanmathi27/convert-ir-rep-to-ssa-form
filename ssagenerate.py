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

# part of lengauer-tarjan algo, find ancestor whose semi-dominator has lowest depfnums
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


# find nth occurence of substr in str (0-indexed)
def findNthOccurrence(string, substr, n):
    start = 0
    for i in range(n + 1):
        pos = string.find(substr, start)
        if pos == -1:
            return -1
        start = pos + 1
    return pos

# return last element of list
def last(x):
    return x[-1] if x else 0

# initialize lists and call renaming
def process():
    cnt = {}
    lisst = {}
    for a in var:
        cnt[a] = 0
        lisst[a] = [0]
    rename(start, lisst, cnt)

def rename(n, lisst, cnt):
    # save stack state at entry
    saved_stacks = {}
    for v in var:
        saved_stacks[v] = len(lisst[v])
    
    # process each instruction in the block
    for k in range(len(n.instr)):
        s = n.instr[k].strip()
        
        if not s:
            continue
        
        # handle phi nodes
        if '$' in s:
            vars_here = returnVar(s)
            if len(vars_here) > 0:
                lhs = vars_here[0]
                # remove any existing subscript
                if '_' in lhs:
                    lhs = lhs[:lhs.find('_')]
                lhs = lhs.strip()
                
                if lhs in cnt:
                    cnt[lhs] += 1
                    i = cnt[lhs]
                    lisst[lhs].append(i)
                    # replace LHS in phi
                    n.instr[k] = re.sub(rf'\b{lhs}\b', f'{lhs}_{i}', n.instr[k], count=1)
            continue
        
        # regular instructions
        original_line = n.instr[k]
        vars_here = returnVar(s)
        
        # check if it's an assignment
        is_assignment = '=' in s and 'if' not in s and len(vars_here) > 0
        
        if is_assignment:
            lhs = vars_here[0]
            rhs_vars = vars_here[1:]
            
            # find where '=' is to split LHS and RHS
            eq_pos = original_line.find('=')
            lhs_part = original_line[:eq_pos]
            rhs_part = original_line[eq_pos:]
            
            # rename RHS variables
            for x in rhs_vars:
                if x in lisst:
                    version = last(lisst[x])
                    rhs_part = re.sub(rf'\b{re.escape(x)}\b', f'{x}_{version}', rhs_part)
            
            # handle LHS definition
            if lhs in cnt:
                cnt[lhs] += 1
                i = cnt[lhs]
                lisst[lhs].append(i)
                # replace LHS (which is still unmodified)
                lhs_part = re.sub(rf'\b{re.escape(lhs)}\b', f'{lhs}_{i}', lhs_part, count=1)
            
            n.instr[k] = lhs_part + rhs_part
            
        else:
            # no assignment, rename all uses
            temp_instr = n.instr[k]
            for x in vars_here:
                if x in lisst:
                    version = last(lisst[x])
                    temp_instr = re.sub(rf'\b{re.escape(x)}\b', f'{x}_{version}', temp_instr)
            n.instr[k] = temp_instr
    
    # fill phi arguments in successors
    for y in n.ch:
        j = None
        for idx, pred in enumerate(pre[y]):
            if pred == n:
                j = idx
                break
        
        if j is None:
            continue
        
        for k in range(len(y.instr)):
            line = y.instr[k]
            if '$' not in line:
                continue
            
            vars_in_phi = returnVar(line)
            if not vars_in_phi:
                continue
            
            phi_var = vars_in_phi[0]
            if '_' in phi_var:
                phi_var = phi_var[:phi_var.find('_')]
            phi_var = phi_var.strip()
            
            if phi_var not in lisst:
                continue
            
            # find the (j+1)-th occurrence of phi_var (skip LHS, count RHS)
            pos = findNthOccurrence(line, phi_var, j + 1)
            if pos != -1:
                version = last(lisst[phi_var])
                # check if it's a whole word match
                if (pos == 0 or not line[pos-1].isalnum()) and \
                   (pos + len(phi_var) >= len(line) or not line[pos + len(phi_var)].isalnum()):
                    y.instr[k] = line[:pos] + f'{phi_var}_{version}' + line[pos + len(phi_var):]
    
    # recurse on dominator tree children
    for x in n.dom:
        if x == n:
            continue
        rename(x, lisst, cnt)
    
    # pop stack
    for v in var:
        while len(lisst[v]) > saved_stacks[v]:
            lisst[v].pop()



def insertPhi(defi, DF, phi, pre):
    # collect definitions
    for n in bl:
        for instr in n.instr:
            instr = instr.strip()
            if not instr or '$' in instr:
                continue
            
            # skip labels without assignments
            if ':' in instr and '=' not in instr:
                continue
            
            vars_here = returnVar(instr)
            if '=' in instr and 'if' not in instr and len(vars_here) > 0:
                v = vars_here[0]
                if v not in defi:
                    defi[v] = set()
                defi[v].add(n)
    
    # insert phi nodes
    for a in var:
        if ':' in a:
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
                    if Y not in defi.get(a, set()):
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


# build the dominator tree
immdom = dominators(start)
for i in immdom:
    if immdom[i] is not None:
        immdom[i].dom.add(i)

# compute dominance frontiers
DF = {}
computeDF(start, DF)

# convert each set of predecessors into a list
for i in pre:
    pre[i] = list(pre[i])

# insert phi-nodes
phi = {}
defi = {}
insertPhi(defi, DF, phi, pre)

# rename variables to finalize SSA
allVar = var
process()

# print out the final SSA form
print('\n\nSSA\n\n')
for blk in bl:
    blk.disp()