#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 10:40:20 2018

@author: mohit
"""
import csv
import numpy as np
from collections import OrderedDict
import constraintFormulation as cf
import time
import glob
import os.path

def readCSV(fileName):
    with open(fileName, 'rU') as csvFile:
        reader = csv.reader(csvFile, delimiter=',')
        data = list(reader)
        data = np.asarray(data)
        return data
        
def cleanData(data):
    variables=[]
    rows, cols = data.shape
#     finding number of variables
    blankRows=0
    while(not data[blankRows,0]):
        blankRows+=1
    blankCols=0
    while(not data[0,blankCols]):
        blankCols+=1
    for i in range(blankRows):
        variables.append(list(OrderedDict.fromkeys(data[i,blankCols:])))
    for i in range(blankCols):
        variables.append(list(OrderedDict.fromkeys(data[blankRows:,i])))
    variables_mat=np.matrix(variables)

    lengths = []
    for i in range(variables_mat.shape[1]):
        lengths.append(len(variables_mat[0,i]))
    dataTensor=np.zeros(lengths)
    
    for i in range(blankRows, rows):
        for j in range(blankCols, cols):
            if data[i,j].astype(int)==1:
                index=()
                for k in range(blankRows):
                    index=index+(variables[k].index(data[k,j]),)
                for k in range(blankCols):
                    index=index+(variables[blankRows+k].index(data[i,k]),)
                dataTensor[index]=1
    return dataTensor,variables

def saveConstraintsForAll(dataTensor,variables,orderingNotImp,ind,num_nurses,directory,tag):
    repeatDim=()
    r=set([v for v in range(len(variables)) if v not in repeatDim])
    subsets=cf.split(r,(),repeatDim)
    with open(os.path.join(directory+"/results", "learnedBounds"+"_"+tag+".csv") ,"a") as my_csv:
        csvWriter = csv.writer(my_csv,delimiter=',')
        if ind==0:
            row=(['']*2)
            for subset in subsets:
                row.extend(subset)
                row.extend(['']*5)
            csvWriter.writerow(row)
        else:
            row=[]
            for l in range(len(subsets)):
                subset=subsets[l]
                newset=subset[0]+subset[1]
                # this value will be used to filter max constraints
                maxPossible=1
                for i in range(len(subset[1])):
                    maxPossible*=len(variables[subset[1][i]])   
                idTensor=cf.tensorIndicator(dataTensor,newset, variables)
                sumSet = range(len(subset[0]),len(newset))
                
                sumTensor_max,sumTensor_min=cf.tensorSum(idTensor,sumSet, np.array(variables)[list(newset)],0)
                row.extend([sumTensor_min])
                row.extend([sumTensor_max])
#                if sumTensor_min==maxPossible:
#                    row.extend([0]) 
#                else:
#                    row.extend([sumTensor_min]) 
                    
#                if sumTensor_max==maxPossible:
#                    row.extend([0]) 
#                else:
#                    row.extend([sumTensor_max]) 
                if len(set(subset[1]))==1 and len(set(orderingNotImp) & set(subset[1]))==0:
                    minConsZero,maxConsZero,minConsNonZero,maxConsNonZero = cf.tensorConsZero(idTensor,sumSet, np.array(variables)[list(newset)])
                    row.extend([minConsZero])
                    row.extend([maxConsZero]) 
#                    if minConsZero==maxPossible:
#                        row.extend([0]) 
#                    else:
#                        row.extend([minConsZero]) 
                        
#                    if maxConsZero==maxPossible:
#                        row.extend([0]) 
#                    else:
#                        row.extend([maxConsZero]) 
#                    row.extend([maxConsZero])
                    row.extend([minConsNonZero])
                    row.extend([maxConsNonZero]) 
#                    if minConsNonZero==maxPossible:
#                        row.extend([0]) 
#                    else:
#                        row.extend([minConsNonZero]) 
                        
#                    if maxConsNonZero==maxPossible:
#                        row.extend([0]) 
#                    else:
#                        row.extend([maxConsNonZero]) 
#                    row.extend([maxConsNonZero])
                    
                else:
                    row.extend(['']*4)
                row.extend([''])
            csvWriter.writerow(row)

def savePref(dataTensor,nurse_preference):
    accept=1
    for i in range(len(nurse_preference)):
        if dataTensor[nurse_preference[i][0],nurse_preference[i][1],i] != 0:
            accept=0
            break
    return accept

def learnConstraintsForAll(directory,num_nurses,extraInfo,bk,mt,hs,test,nurse_preference):
    tag=str(bk)+str(mt)+str(hs)
#    start=time.clock()
    ind=0
    prefSatisfaction=[]
    for fl in glob.glob(directory+'/solutions/*.csv'):
        data = readCSV(fl)
        dataTensor,variables=cleanData(data)
        lenVar=[]
        for i in range(len(variables)):
            lenVar.append(len(variables[i]))
        orderingNotImp=[2]
        if ind==0:
            saveConstraintsForAll(dataTensor,variables,orderingNotImp,0,num_nurses,directory,tag+str(0))
        saveConstraintsForAll(dataTensor,variables,orderingNotImp,1,num_nurses,directory,tag+str(0))
        
        skillset=np.zeros([2,num_nurses])
        skillset[0]=extraInfo
        skillset[1]=[int(x==0) for x in extraInfo]
        
        if bk==1:
            for i in range(2):
                if i==0:
                    tmp=extraInfo
                if i==1:
                    tmp=[int(x==0) for x in extraInfo]
                skillset=np.zeros([num_nurses,int(sum(tmp))])
                k=0
                for j in range(len(tmp)):
                    if tmp[j]==1:
                        skillset[j][k]=1
                        k+=1
                        
                dim=2
                updatedVariables=variables[:]
                updatedVariables[dim]=[x for x, y in zip(variables[dim], tmp) if y == 1]
                mat=np.tensordot(dataTensor,skillset, [dim,0])
                if ind==0:
                    saveConstraintsForAll(mat,updatedVariables,orderingNotImp,0,num_nurses,directory,tag+str(0)+str(i))
                saveConstraintsForAll(mat,updatedVariables,orderingNotImp,1,num_nurses,directory,tag+str(0)+str(i))
        ind+=1
        
        if test==1:
            prefSatisfaction.append(savePref(dataTensor,nurse_preference))
    
#    print("\nTime Taken: ",time.clock()-start,' secs')
    return prefSatisfaction
