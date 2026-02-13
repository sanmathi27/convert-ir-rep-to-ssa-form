#generation of cfg basic blocks

#so, we read script ; identify block leaders based on 'goto' and 'if' and extract block names from here
#we create the basic block, add edges ; original vars are identified ; cfg printed

import re

class block:
    def __init__(self, n):
        self.name = n #block name B1, B2 etc
        self.instr = [] #list of instrs in that block
        self.oriv = set() #variables used in the block
        self.ch = [] #children blocks
        self.dom = set([self]) # dominators, initially only itself

    def disp(self): # display the instructions in the block
        print(f"\n{self.name}")
        for i in self.instr:
            print(i)

    def children(self): # display the children of the block
        for child in self.ch:
            if child is not None :
                print(f"{self.name} -> {child.name}")



var = set()
with open("test.txt", "r") as f:
    s = f.read().split('\n')

l = [0]  # line numbers of leaders
blnum = []  # list of target labels L1, L2 etc
n = len(s) # number of lines in input

# identify leaders
for i in range(n):
    line = s[i] #ith line in input

    if 'if ' in line and 'goto' in line:
        # conditional jump: next line is fall-through leader
        l.append(i + 1)  # fall-through
        label = line[line.find('goto ') + 5:].strip()
        blnum.append(label)

    elif 'goto' in line:
        # inconditional jump: next line is fall-through leader
        l.append(i + 1)
        label = line[line.find('goto ') + 5:].strip()
        blnum.append(label)

# add label lines
for label in blnum:
    for x in range(n):
        if s[x].strip().startswith(label + ':'):
            l.append(x)

l = sorted(set(l))

cur = None
start = None
bl = [] # list of blocks
b = {} #label->block
j = 1 # block counter

for i in range(n):
    if i in l: # if line is a leader
        cur = block('B' + str(j)) # create a new block
        bl.append(cur)
        if ':' in s[i]:  # if line is a label
            label_name = s[i].strip().split(':')[0]  # extract label without colon
            b[label_name] = cur # map label to block
        if start is None:
            start = cur # first block
        j += 1

    cur.instr.append(s[i])
    
    # extract variables from the line
    x = s[i].split('goto')[0] if 'goto' in s[i] else s[i]
    # skip label prefix 
    x = re.sub(r'^\s*\w+:\s*', '', x)

    for k in re.findall(r'\b\w+\b', x):
        if k == 'if' or k.isnumeric():
            continue
        # skip labels like L1, L2, L3
        if re.match(r'^L\d+$', k):
            continue
        cur.oriv.add(k)
        var.add(k)



# resolve jump edges for all blocks
for idx, blk in enumerate(bl):
    if not blk.instr: 
        continue

    last = blk.instr[-1] # last instruction in the block

    if 'if' in last and 'goto' in last:
        # conditional branch: both true (goto) and false (fall-through)
        target_label = last[last.find('goto ') + 5:].strip()  
        true_branch = b.get(target_label)
        if true_branch and true_branch not in blk.ch:
            blk.ch.append(true_branch)

        # fall-through block
        if idx + 1 < len(bl):
            fallthrough = bl[idx + 1]
            if fallthrough not in blk.ch:
                blk.ch.append(fallthrough)

    elif 'goto' in last:
        # unconditional branch (no fall-through)
        target_label = last[last.find('goto ') + 5:].strip()  
        jump_block = b.get(target_label)
        if jump_block and jump_block not in blk.ch:
            blk.ch.append(jump_block)

    else:
        # no jump: fall-through to next block
        if idx + 1 < len(bl):
            next_block = bl[idx + 1]
            if next_block not in blk.ch:
                blk.ch.append(next_block)


# print CFG
print('CFG\n')
for block in bl:
    block.disp()

print('\nCFG Edges:')
for block in bl:
    block.children()

print('\nVariables:')
for i in var:
    print(i)