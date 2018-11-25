#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:45:50 2018

@author: mohit
"""

import sampler
import countor
import numpy as np
import glob
import os
import csv
from scipy import stats
import random
import time
import sys
from os.path import expanduser

def readBounds(file,num_constrType,num_constr):
    data=countor.readCSV(file)
    data_transpose=list(zip(*data))
    data_int=np.zeros([len(data_transpose),len(data_transpose[0])-1])
    for i in range(len(data_transpose)):
        for j in range(1,len(data_transpose[i])):
            if data_transpose[i][j]!='':
                data_int[i,j-1]=int(data_transpose[i][j])
    
    bounds_tr=np.zeros([len(data_int[0]),num_constrType,num_constr])
    for j in range(len(data_int[0])):
        k=0
        for i in range(83):
            if (i+1)%7 != 0:
                bounds_tr[j,int(k/6),k%6]=data_int[i,j]
                k+=1
    return bounds_tr.astype(np.int64)

def aggrBounds(selbounds,num_constrType,num_constr,constrMaxval):
    bounds_learned=np.zeros([num_constrType,num_constr])
    for i in range(num_constrType):
        for j in range(num_constr):
            row=int((i*num_constr+j)/6)
            col=(i*num_constr+j)%6
            if j%2==0:
                bounds_learned[row,col]=np.min(selbounds[:,i,j])
            if j%2!=0:
                bounds_learned[row,col]=np.max(selbounds[:,i,j])
                if bounds_learned[row,col]==constrMaxval[i]:
                    bounds_learned[row,col]=0
    return bounds_learned.astype(np.int64)

###########checks if bound2 is more constrained than bound1##################
def moreConstrained(bound1,bound2,num_constrType,num_constr):
    output=1
    for i in range(num_constrType):
        for j in range(num_constr):
            if bound1[i,j]==0:
                continue
            if j%2==0 and bound2[i,j]<bound1[i,j]:
                output=0
                break
            if j%2==1 and bound2[i,j]>bound1[i,j]:
                output=0
                break
            if j%2==1 and bound2[i,j]==0 and bound1[i,j]>0:
                output=0
                break
        if output==0:
            break
    return output

home = expanduser("~")

numSam=int(sys.argv[1])
bk=int(sys.argv[2])
mt=int(sys.argv[3])
hs=int(sys.argv[4])

extraConstPerc = 10

numFiles=numSam

tag=str(bk)+str(mt)+str(hs)+"_"+str(numSam)

directory=os.getcwd()+'/data/filterPerf/'+tag
if not os.path.exists(directory):
    os.makedirs(directory)

num_nurses=15
num_days=7
num_shifts=3   
orderingNotImp=[2]

num_constrType=12
num_constr=6

constrList=[[(0,),(1,)],[(0,),(2,)],[(0,),(1,2)],[(1,),(0,)],[(1,),(2,)],[(1,),(0,2)],[(2,),(0,)],[(2,),(1,)],[(2,),(0,1)],[(0,1),(2,)],[(0,2),(1,)],[(1,2),(0,)]]

tbounds=np.zeros([num_constrType,num_constr])
tbounds0=np.zeros([num_constrType,num_constr])
tbounds1=np.zeros([num_constrType,num_constr])
if hs==0:
    num_nurses=10
    num_days=28
    num_shifts=4   
    tbounds[2,0]=4
    tbounds[2,1]=6
    tbounds[6,2]=1
    tbounds[6,3]=7
    tbounds[6,4]=2  
    tbounds[9,0]=1
    tbounds[9,1]=2
    tbounds[10,1]=1 
    
    if bk==0:
        tbounds[6,0]=9
        tbounds[6,1]=16
        tbounds[6,5]=8 
    
    if bk==1:
        tbounds0[6,0]=9
        tbounds0[6,1]=16
        tbounds0[6,5]=8   
        
        tbounds1[6,0]=4
        tbounds1[6,1]=9
        tbounds1[6,5]=4 
    
if hs==1:
    num_nurses=31
    num_days=28
    num_shifts=4   
    tbounds[2,0]=16
    tbounds[2,1]=24
    tbounds[6,2]=1
    tbounds[6,4]=2 
    tbounds[9,0]=2
    tbounds[9,1]=9
    tbounds[10,1]=1
    
    if bk==0:
        tbounds[6,0]=6
        tbounds[6,1]=16
        tbounds[6,3]=7
        tbounds[6,5]=8  
    
    if bk==1:
        tbounds0[6,0]=4
        tbounds0[6,1]=13
        tbounds0[6,3]=8
        tbounds0[6,5]=4   
        
        tbounds1[6,0]=6
        tbounds1[6,1]=16
        tbounds1[6,3]=7
        tbounds1[6,5]=8
    
if hs==2:
    num_nurses=49
    num_days=28
    num_shifts=4   
    tbounds[2,0]=20
    tbounds[2,1]=29
    tbounds[6,2]=1  
    tbounds[9,0]=1
    tbounds[9,1]=8
    tbounds[10,1]=1
    
    if bk==0:
        tbounds[6,0]=6
        tbounds[6,1]=16
        tbounds[6,3]=5
        tbounds[6,4]=1
        tbounds[6,5]=7 
    
    if bk==1:
        tbounds0[6,0]=6
        tbounds0[6,1]=16
        tbounds0[6,3]=5
        tbounds0[6,4]=1
        tbounds0[6,5]=7   
        
        tbounds1[6,0]=3
        tbounds1[6,1]=10
        tbounds1[6,3]=8
        tbounds1[6,4]=2
        tbounds1[6,5]=5 
    
tbounds=tbounds.astype(np.int64)
target_cc=np.count_nonzero(tbounds)

if bk==1:
    tbounds0=tbounds0.astype(np.int64)
    tbounds1=tbounds1.astype(np.int64)
    target_cc+=np.count_nonzero(tbounds0)
    target_cc+=np.count_nonzero(tbounds1)

dimSize=[num_days,num_shifts,num_nurses]
constrMaxval=[]
for val in constrList:
    tot=1
    for i in range(len(val[1])):
        tot*=dimSize[int(val[1][i])]
    constrMaxval.append(tot)
print(constrMaxval)

soln=directory+"/solutions"
result=directory+"/results"

if not os.path.exists(soln):
    os.makedirs(soln)
if not os.path.exists(result):
    os.makedirs(result)
   
nurse_skill=np.zeros(num_nurses)
if bk==1:            
    for i in range(num_nurses):
        random.seed(i)
        nurse_skill[i]=random.randint(0,1)
#    print(nurse_skill)
nurse_preference={}
if mt==1:
    n=int(np.round(num_nurses*extraConstPerc/100))
    target_cc+=n
    for i in range(n):
        random.seed(i)
        nurse_preference[i]=(random.randint(0,num_days-1),random.randint(0,num_shifts-1)) 
            
for fl in glob.glob(soln+"/*.csv"): 
      os.remove(fl) 
print("\nGenerating samples using ",target_cc," constraints")
start=time.clock()
sampler.generateSample(num_nurses,num_days,num_shifts,numSam,extraConstPerc,nurse_skill,nurse_preference,tbounds,tbounds0,tbounds1,soln,bk,mt)
print("Generated ",numSam," samples in ",time.clock()-start," secs")

for fl in glob.glob(result+"/*.csv"): 
      os.remove(fl) 

start=time.clock()
countor.learnConstraintsForAll(directory,num_nurses,nurse_skill,bk,mt,hs,0,nurse_preference)
timeTaken=time.clock()-start
print("\nLearned bounds for ",numSam," samples in ",timeTaken,' secs')

tag=str(bk)+str(mt)+str(hs)
file=result+"/learnedBounds"+"_"+tag+"0.csv"
lbounds=readBounds(file,num_constrType,num_constr)

if bk==1:
    file=result+"/learnedBounds"+"_"+tag+"00.csv"
    lbounds0=readBounds(file,num_constrType,num_constr)
    
    file=result+"/learnedBounds"+"_"+tag+"01.csv"
    lbounds1=readBounds(file,num_constrType,num_constr)


bounds_prev=np.zeros([num_constrType,num_constr])
bounds_prev0=np.zeros([num_constrType,num_constr])
bounds_prev1=np.zeros([num_constrType,num_constr])
prec_prev=0
rec_prev=0
time_prev=0

prevSol=0
numSeed=4
selectedRows=[[] for _ in range(numSeed)]

my_csv = open(directory+ "/results.csv" ,"w+")
csvWriter = csv.writer(my_csv,delimiter=',')
row=['BK','MT', 'HS','target','numSol','learned','learned_err']
csvWriter.writerow(row) 

for numSol in [1,10,25,50]:
    print("\n############ Number of examples used: ",numSol," ############")
    
    usedCons=np.zeros(numSeed)
    
    for seed in range(numSeed):
        random.seed(seed)
        selRows = selectedRows[seed] + random.sample([x for x in range(0,numSam) if x not in selectedRows[seed]],numSol-prevSol)
        selectedRows[seed]=selRows
        selbounds=np.array([lbounds[i] for i in selRows])
        start=time.clock()
        bounds_learned=aggrBounds(selbounds,num_constrType,num_constr,constrMaxval)
        learned_cc=np.count_nonzero(bounds_learned)
        
        bounds_learned0=np.zeros([num_constrType,num_constr])
        bounds_learned1=np.zeros([num_constrType,num_constr])
        if bk==1:
            selbounds0=np.array([lbounds0[i] for i in selRows])
            selbounds1=np.array([lbounds1[i] for i in selRows])
            print(selbounds.shape)
            print(selbounds1.shape)
            bounds_learned0=aggrBounds(selbounds0,num_constrType,num_constr,constrMaxval)
            bounds_learned1=aggrBounds(selbounds1,num_constrType,num_constr,constrMaxval)
            learned_cc+=np.count_nonzero(bounds_learned0)
            learned_cc+=np.count_nonzero(bounds_learned1)
        print("\nGenerating samples using ",learned_cc," constraints")
        usedCons[seed]=learned_cc
        
    row=[]
    row.extend([bk])
    row.extend([mt])
    row.extend([hs])
    row.extend([target_cc])
    row.extend([numSol])
    row.extend([sum(usedCons)/numSeed])
    row.extend([np.std(usedCons)/np.sqrt(numSeed)])
    csvWriter.writerow(row)
        
my_csv.close()   
