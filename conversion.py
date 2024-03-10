#generation of cfg basic blocks

#so, we read script ; identify block leaders based on 'goto' and extarct block names form here
#we create the basic block, add edges ;  original vars are identified ; cfg printed

#ive ignored the 'if' for the leaders recognition, sorry

import re  # for identifying regular exps


#class rep for basic blocks
class block:
    def __init__(self,n):
        self.name=n #block name
        self.instr=[] #instructions in each basic block
        self.oriv=set() #original variables
        self.ch=[] #child node
        self.dom=set([self]) #dominance frontier

    def disp(self):
        print()
        print(self.name)
        
        for i in self.instr:
            print(i)

#read input file
var=set() #for the variables seen
f = open("test.txt", "r")
t=f.read()
l=[0] #list to store line number for the leaders
blnum=[] #basic block number
s=t.split('\n')

for i in range(len(s)):
    if 'goto ' in s[i]:
        # if 'goto' statement is found, add next line as leader
        l.append(i+1)
        # extract the block name after 'goto' and add it to block names
        blnum.append(s[i][s[i].find('goto ')+5:])
        
#add actual block name as leaders
for i in blnum:
    l=l+list(filter(lambda x: i+':' in s[x],range(len(s))))
        
l.sort()

j=1
cur=None
start=None #start block
b={} #block dict
bl=[] #list to store blocks
for i in range(len(s)):
    if i in l:#if line num is leader, create block
        temp=cur
        cur=block('B'+str(j))
        bl.append(cur)
        b[s[i].strip()]=cur
        #set start block, if its first block, or append new block as child of prev block
        if temp==None:
            start=cur
        else:
            temp.ch.append(cur)
        j=j+1
    cur.instr.append(s[i]) # add inst to the current block
    x=s[i]
    if s[i].find('goto ')!=-1:#extract blck name afetr 'goto'
        x=s[i][:s[i].find('goto ')]
    #find all vars in the inst and arr to oriv(original variables)
    for k in re.findall('\w\w*:?',x):
        if k=='if' or k.isnumeric() or ':' in k:
            continue
        cur.oriv |= {k}
        var=var.union({k})


cur=start
temp=cur
while cur!=None:
    #surf through cfg and add edges based on the 'goto' stats
    if len(cur.ch)>0:
        temp=cur.ch[0]
    else:
        temp=None
    i=cur.instr[len(cur.instr)-1]
    if 'goto' in i:
        if 'if ' not in i:
            cur.ch=[b[i[i.find('goto ')+5:].strip()+':']]
        else:
            cur.ch.append(b[i[i.find('goto ')+5:].strip()+':'])

    cur=temp

print('CFG\n\n')
for i in bl:
    i.disp()
