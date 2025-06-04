#generation of cfg basic blocks

#so, we read script ; identify block leaders based on 'goto' and extarct block names form here
#we create the basic block, add edges ;  original vars are identified ; cfg printed

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



# Read input file
var = set()
with open("test.txt", "r") as f:
    s = f.read().split('\n')

l = [0]  # line numbers of leaders
blnum = []  # list of target labels L1, L2 etc
n = len(s) # number of lines in input

# Identify leaders
for i in range(n):
    line = s[i] #ith line in input

    if 'if ' in line and 'goto' in line:
        # Conditional jump: Conditional jump — next line is fall-through leader
        l.append(i + 1)  # fall-through
        label = line[line.find('goto ') + 5:].strip()
        blnum.append(label)

    elif 'goto' in line:
        # Unconditional jump: next line is fall-through leader
        l.append(i + 1)
        label = line[line.find('goto ') + 5:].strip()
        blnum.append(label)

# Add label lines
for label in blnum:
    for x in range(n):
        if s[x].strip().startswith(label + ':'):
            l.append(x)

l = sorted(set(l))

# Build basic blocks
cur = None
start = None
bl = [] # list of blocks
b = {} #label->block
j = 1 # block counter

for i in range(n):
    if i in l: # if line is a leader
        temp = cur
        cur = block('B' + str(j)) # create a new block
        bl.append(cur)
        if ':' in s[i]:  # if line is a label
            label_name = s[i].strip().split(':')[0] + ':'  # ensure it's like 'L1:'
            b[label_name] = cur # map label to block
        if temp is None:
            start = cur # first block
        else:
            #if prev block doesnt end in unconditional goto, connect it to current new block
            if 'goto' not in temp.instr[-1] or ('if' in temp.instr[-1]):
                temp.ch.append(cur)
        j += 1

    cur.instr.append(s[i])
    x = s[i].split('goto')[0] if 'goto' in s[i] else s[i]

# Skip label lines (e.g., "L1: x = 1")
    x = re.sub(r'^\s*\w+:\s*', '', x)

    for k in re.findall(r'\b\w+\b', x):
        if k == 'if' or k.isnumeric():
            continue
    # Skip labels like L1, L2, L3
        if re.match(r'^L\d+$', k):
            continue
        cur.oriv.add(k)
        var.add(k)



# Resolve jump edges for all blocks
for idx, blk in enumerate(bl):
    if not blk.instr: # Skip empty blocks
        continue

    last = blk.instr[-1] # Last instruction in the block

    if 'if' in last and 'goto' in last:
        # Conditional branch: both true (goto) and false (fall-through)
        target_label = last[last.find('goto ') + 5:].strip() + ':'
        true_branch = b.get(target_label)
        if true_branch and true_branch not in blk.ch:
            blk.ch.append(true_branch)

        # Fall-through block
        if idx + 1 < len(bl):
            fallthrough = bl[idx + 1]
            if fallthrough not in blk.ch:
                blk.ch.append(fallthrough)

    elif 'goto' in last:
        # Unconditional branch
        target_label = last[last.find('goto ') + 5:].strip() + ':'
        jump_block = b.get(target_label)
        if jump_block:
            blk.ch = [jump_block]

    else:
        # No jump: fall-through to next block
        if idx + 1 < len(bl):
            next_block = bl[idx + 1]
            if next_block not in blk.ch:
                blk.ch.append(next_block)


# Print CFG
print('CFG\n')
for block in bl:
    block.disp()

print('\nCFG Edges:')
for block in bl:
    block.children()

for i in var:
    print(i)
