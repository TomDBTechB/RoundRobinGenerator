#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 10:58:20 2018

@author: mohit
"""
import os
import random
import csv
import numpy as np
from gurobipy import *
import os.path
    
def generateSample(num_nurses,num_days,num_shifts,numSam,bounds,directory):
#    print(bounds)
    
    N=list(range(num_nurses))
    D=list(range(num_days))
    Ds=list(range(num_days+1))
    S=list(range(num_shifts))
    Ss=list(range(num_shifts+1))
    Sk=list(range(2))
    variables=[D,S,N]
    
    num_constrType=12
    num_constr=6
    constrList=[[(0,),(1,)],[(0,),(2,)],[(0,),(1,2)],[(1,),(0,)],[(1,),(2,)],[(1,),(0,2)],[(2,),(0,)],[(2,),(1,)],[(2,),(0,1)],[(0,1),(2,)],[(0,2),(1,)],[(1,2),(0,)]]

    #Forbidden Shift Successions
    F=[(num_shifts-1,0)]
        
    #Weekends
    W=[(5,6)]
    

    rSam=0
    tSam=0
    lSam=0
        
    try:
        m=Model("nspSolver")
        m.setParam(GRB.Param.OutputFlag,0)
        ########### Decision Variables #############
        x = m.addVars(N,D,S,Sk, vtype=GRB.BINARY, name="x")
        o = m.addVars(N,D,S, vtype=GRB.BINARY, name="o")
        p = m.addVars(N,D, vtype=GRB.BINARY, name="p")
        q = m.addVars(N,S, vtype=GRB.BINARY, name="q")
        r = m.addVars(S,D, vtype=GRB.BINARY, name="r")

        tw = m.addVars(N,D,D, vtype=GRB.BINARY, name="tw")
        sw = m.addVars(N,Ds,D, vtype=GRB.BINARY, name="sw")
        tw1 = m.addVars(N,D,S,D, vtype=GRB.BINARY, name="tw1")
        sw1 = m.addVars(N,Ds,S,D, vtype=GRB.BINARY, name="sw1")
        
        
        tws = m.addVars(N,S,S, vtype=GRB.BINARY, name="tws")
        sws = m.addVars(N,Ss,S, vtype=GRB.BINARY, name="sws")
        tfs = m.addVars(N,S,S, vtype=GRB.BINARY, name="tfs")
        sfs = m.addVars(N,Ss,S, vtype=GRB.BINARY, name="sfs")
        
        tf = m.addVars(N,D,D, vtype=GRB.BINARY, name="tf")
        sf = m.addVars(N,Ds,D, vtype=GRB.BINARY, name="sf")
        tw1f = m.addVars(N,D,S,D, vtype=GRB.BINARY, name="tw1f")
        sw1f = m.addVars(N,Ds,S,D, vtype=GRB.BINARY, name="sw1f")
        
        ########### Required Constraints #############
        m.addConstrs(
                (o.sum(n,d,'*') == p[n,d] 
                for n in N for d in D),"po")
        
        m.addConstrs((x.sum(n,d,s,'*')==o[n,d,s] for n in N for d in D for s in S),"xo")        
#        m.addConstrs((x[n,d,s,sk]==o[n,d,s] for n in N for d in D for s in S for sk in Sk if nurse_skill[n]==sk),"xo")
#        m.addConstrs((x[n,d,s,sk]==0 for n in N for d in D for s in S for sk in Sk if nurse_skill[n]!=sk),"xo")
        m.addConstrs((q[n,s] <= o.sum(n,'*',s) for n in N for s in S ),"qo")
        m.addConstrs((q[n,s]*o.sum(n,'*',s) == o.sum(n,'*',s) for n in N for s in S ),"qo")
        m.addConstrs((r[s,d] <= o.sum('*',d,s) for d in D for s in S ),"ro")
        m.addConstrs((r[s,d]*o.sum('*',d,s) == o.sum('*',d,s) for d in D for s in S ),"ro")
        
        ########### Hard Constraints #############
#        print(bounds)
        for i in range(len(bounds)):
            if bounds[i,0]>0:
#                print(bounds[i,0])
                if constrList[i]==[(0,),(1,)]:
                    m.addConstrs((r.sum('*',d) >= bounds[i,0] for d in D),"constr")
                    
                elif constrList[i]==[(0,),(2,)]:
                    m.addConstrs((p.sum('*',d) >= bounds[i,0] for d in D),"constr")
                    
                elif constrList[i]==[(0,),(1,2)]:
                    m.addConstrs((o.sum('*',d,'*') >= bounds[i,0] for d in D),"constr")
                    
                elif constrList[i]==[(1,),(0,)]:
                    m.addConstrs((r.sum(s,'*') >= bounds[i,0] for s in S),"constr")
                    
                elif constrList[i]==[(1,),(2,)]:
                    m.addConstrs((q.sum('*',s) >= bounds[i,0] for s in S),"constr")
                    
                elif constrList[i]==[(1,),(0,2)]:
                    m.addConstrs((o.sum('*','*',s) >= bounds[i,0] for s in S),"constr")
                    
                elif constrList[i]==[(2,),(0,)]:
                    m.addConstrs((p.sum(n,'*') >= bounds[i,0] for n in N),"constr")
                    
                elif constrList[i]==[(2,),(1,)]:
                    m.addConstrs((q.sum(n,'*') >= bounds[i,0] for n in N),"constr")
                    
                elif constrList[i]==[(2,),(0,1)]:
                    m.addConstrs((o.sum(n,'*','*') >= bounds[i,0] for n in N),"constr")
                    
                elif constrList[i]==[(0,1),(2,)]:
                    m.addConstrs((o.sum('*',d,s) >= bounds[i,0] for d in D for s in S),"constr")
                    
                elif constrList[i]==[(0,2),(1,)]:
                    m.addConstrs((o.sum(n,d,'*') >= bounds[i,0] for d in D for n in N),"constr")
                    
                elif constrList[i]==[(1,2),(0,)]:
                    m.addConstrs((o.sum(n,'*',s) >= bounds[i,0] for n in N for s in S),"constr")
                    
            if bounds[i,1]>0:
#                print(bounds[i,1])
                if constrList[i]==[(0,),(1,)]:
                    m.addConstrs((r.sum('*',d) <= bounds[i,1] for d in D),"constr")
                    
                elif constrList[i]==[(0,),(2,)]:
                    m.addConstrs((p.sum('*',d) <= bounds[i,1] for d in D),"constr")
                    
                elif constrList[i]==[(0,),(1,2)]:
                    m.addConstrs((o.sum('*',d,'*') <= bounds[i,1] for d in D),"constr")
                    
                elif constrList[i]==[(1,),(0,)]:
                    m.addConstrs((r.sum(s,'*') <= bounds[i,1] for s in S),"constr")
                    
                elif constrList[i]==[(1,),(2,)]:
                    m.addConstrs((q.sum('*',s) <= bounds[i,1] for s in S),"constr")
                    
                elif constrList[i]==[(1,),(0,2)]:
                    m.addConstrs((o.sum('*','*',s) <= bounds[i,1] for s in S),"constr")
                    
                elif constrList[i]==[(2,),(0,)]:
                    m.addConstrs((p.sum(n,'*') <= bounds[i,1] for n in N),"constr")
                    
                elif constrList[i]==[(2,),(1,)]:
                    m.addConstrs((q.sum(n,'*') <= bounds[i,1] for n in N),"constr")
                    
                elif constrList[i]==[(2,),(0,1)]:
                    m.addConstrs((o.sum(n,'*','*') <= bounds[i,1] for n in N),"constr")
                    
                elif constrList[i]==[(0,1),(2,)]:
                    m.addConstrs((o.sum('*',d,s) <= bounds[i,1] for d in D for s in S),"constr")
                    
                elif constrList[i]==[(0,2),(1,)]:
                    m.addConstrs((o.sum(n,d,'*') <= bounds[i,1] for d in D for n in N),"constr")
                    
                elif constrList[i]==[(1,2),(0,)]:
                    m.addConstrs((o.sum(n,'*',s) <= bounds[i,1] for n in N for s in S),"constr")
            
#        if mt==1:
#            for i in range(len(nurse_preference)):
#                m.addConstr((o[i,nurse_preference[i][0],nurse_preference[i][1]] == 0),"nursePref")
            
        if bounds[6,5] + bounds[6,4] >0:
            m.addConstrs(( tw[n,0,0] == p[n,0] for n in N), "MaxConsWork")
            m.addConstrs(( tw[n,d1+1,0] <= p[n,d1+1]
                    for n in N for d1 in D if d1<len(D)-1), "MaxConsWork")
            m.addConstrs(( tw[n,d1+1,0] <= 1-p[n,d1]
                    for n in N for d1 in D if d1<len(D)-1), "MaxConsWork")
            m.addConstrs(( tw[n,d1+1,0] >= p[n,d1+1]-p[n,d1]
                    for n in N for d1 in D if d1<len(D)-1), "MaxConsWork")
            
            m.addConstrs(( tw[n,0,d2] == 0
                    for n in N for d2 in D if d2>0), "MaxConsWork")
            m.addConstrs(( tw[n,d1,d2] <= tw[n,d1-1,d2-1]
                    for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsWork")
            m.addConstrs(( tw[n,d1,d2] <= p[n,d1]
                    for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsWork")
            m.addConstrs(( tw[n,d1,d2] >= p[n,d1]+tw[n,d1-1,d2-1]-1
                    for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsWork")
            if bounds[6,5]>0:
                m.addConstr(
                        (quicksum(tw[n,d1,d2] for n in N for d1 in D for d2 in range(bounds[6,5],len(D)))==0),"maxconswork"
                        )
            if bounds[6,4]>0:
                m.addConstrs(( sw[n,0,d2] == 0
                        for n in N for d2 in D), "MinConsWork")
                m.addConstrs(( sw[n,d1,d2] <= tw[n,d1-1,d2]
                        for n in N for d1 in D for d2 in D if d1>0), "MinConsWork")
                m.addConstrs(( sw[n,d1,d2] <= 1-p[n,d1]
                        for n in N for d1 in D for d2 in D if d1>0), "MinConsWork")
                m.addConstrs(( sw[n,d1,d2] >= tw[n,d1-1,d2]-p[n,d1]
                        for n in N for d1 in D for d2 in D if d1>0), "MinConsWork")
                
                m.addConstrs(( sw[n,num_days,d2] == tw[n,num_days-1,d2]
                        for n in N for d2 in D), "MinConsWork")
                
                m.addConstr(
                        (quicksum(sw[n,d1,d2]*(bounds[6,4]-1-d2) for n in N for d1 in Ds for d2 in range(bounds[6,4]-1))==0),"minconswork"
                        )
        
        if bounds[6,3] + bounds[6,2]>0:
            m.addConstrs(( tf[n,0,0] == 1-p[n,0] for n in N), "MaxConsFree")
            m.addConstrs(( tf[n,d1+1,0] <= p[n,d1]
                    for n in N for d1 in D if d1<len(D)-1), "MaxConsFree")
            m.addConstrs(( tf[n,d1+1,0] <= 1-p[n,d1+1]
                    for n in N for d1 in D if d1<len(D)-1), "MaxConsFree")
            m.addConstrs(( tf[n,d1+1,0] >= p[n,d1]-p[n,d1+1]
                    for n in N for d1 in D if d1<len(D)-1), "MaxConsFree")
            
            m.addConstrs(( tf[n,0,d2] == 0
                    for n in N for d2 in D if d2>0), "MaxConsFree")
            m.addConstrs(( tf[n,d1,d2] <= tf[n,d1-1,d2-1]
                    for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsFree")
            m.addConstrs(( tf[n,d1,d2] <= 1-p[n,d1]
                    for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsFree")
            m.addConstrs(( tf[n,d1,d2] >= tf[n,d1-1,d2-1]-p[n,d1]
                    for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsFree")
            if bounds[6,3]>0:
                m.addConstr(
                        (quicksum(tf[n,d1,d2] for n in N for d1 in D for d2 in range(bounds[6,3],len(D)))==0),"maxconsfree"
                        )
            
            if bounds[6,2]>0:
                m.addConstrs(( sf[n,0,d2] == 0
                        for n in N for d2 in D), "MinConsFree")
                m.addConstrs(( sf[n,d1,d2] <= tf[n,d1-1,d2]
                        for n in N for d1 in D for d2 in D if d1>0), "MinConsFree")
                m.addConstrs(( sf[n,d1,d2] <= p[n,d1]
                        for n in N for d1 in D for d2 in D if d1>0), "MinConsFree")
                m.addConstrs(( sf[n,d1,d2] >= tf[n,d1-1,d2]+p[n,d1]-1
                        for n in N for d1 in D for d2 in D if d1>0), "MinConsFree")
                
                
                m.addConstrs(( sf[n,num_days,d2] == tf[n,num_days-1,d2]
                        for n in N for d2 in D), "MinConsFree")
                
                m.addConstr(
                        (quicksum(sf[n,d1,d2]*(bounds[6,2]-1-d2) for n in N for d1 in Ds for d2 in range(bounds[6,2]-1))==0),"minconsfree"
                        )    
        
        if bounds[7,5] + bounds[7,4] > 0:
            m.addConstrs(( tws[n,0,0] == q[n,0] for n in N), "MaxConsWork")
            m.addConstrs(( tws[n,s1+1,0] <= q[n,s1+1]
                    for n in N for s1 in S if s1<len(S)-1), "MaxConsWork")
            m.addConstrs(( tws[n,s1+1,0] <= 1-q[n,s1]
                    for n in N for s1 in S if s1<len(S)-1), "MaxConsWork")
            m.addConstrs(( tws[n,s1+1,0] >= q[n,s1+1]-q[n,s1]
                    for n in N for s1 in S if s1<len(S)-1), "MaxConsWork")
            
            m.addConstrs(( tws[n,0,s2] == 0
                    for n in N for s2 in S if s2>0), "MaxConsWork")
            m.addConstrs(( tws[n,s1,s2] <= tws[n,s1-1,s2-1]
                    for n in N for s1 in S for s2 in S if s1>0 if s2>0), "MaxConsWork")
            m.addConstrs(( tws[n,s1,s2] <= q[n,s1]
                    for n in N for s1 in S for s2 in S if s1>0 if s2>0), "MaxConsWork")
            m.addConstrs(( tws[n,s1,s2] >= q[n,s1]+tws[n,s1-1,s2-1]-1
                    for n in N for s1 in S for s2 in S if s1>0 if s2>0), "MaxConsWork")
            
            if bounds[7,5]>0:
                m.addConstr(
                        (quicksum(tws[n,s1,s2] for n in N for s1 in S for s2 in range(bounds[7,5],len(S)))==0),"maxconswork"
                        )
        
            if bounds[7,4]>0:
                m.addConstrs(( sws[n,0,s2] == 0
                        for n in N for s2 in S), "MinConsWork")
                m.addConstrs(( sws[n,s1,s2] <= tws[n,s1-1,s2]
                        for n in N for s1 in S for s2 in S if s1>0), "MinConsWork")
                m.addConstrs(( sws[n,s1,s2] <= 1-q[n,s1]
                        for n in N for s1 in S for s2 in S if s1>0), "MinConsWork")
                m.addConstrs(( sws[n,s1,s2] >= tws[n,s1-1,s2]-q[n,s1]
                        for n in N for s1 in S for s2 in S if s1>0), "MinConsWork")
                
                m.addConstrs(( sws[n,num_shifts,s2] == tws[n,num_shifts-1,s2]
                        for n in N for s2 in S), "MinConsWork")
                
                m.addConstr(
                        (quicksum(sws[n,s1,s2]*(bounds[7,4]-1-s2) for n in N for s1 in Ss for s2 in range(bounds[7,4]-1))==0),"minconswork"
                        )
        
        if bounds[7,3]+bounds[7,2]>0:
            m.addConstrs(( tfs[n,0,0] == 1-q[n,0] for n in N), "MaxConsFree")
            m.addConstrs(( tfs[n,s1+1,0] <= q[n,s1]
                    for n in N for s1 in S if s1<len(S)-1), "MaxConsFree")
            m.addConstrs(( tfs[n,s1+1,0] <= 1-q[n,s1+1]
                    for n in N for s1 in S if s1<len(S)-1), "MaxConsFree")
            m.addConstrs(( tfs[n,s1+1,0] >= q[n,s1]-q[n,s1+1]
                    for n in N for s1 in S if s1<len(S)-1), "MaxConsFree")
            
            m.addConstrs(( tfs[n,0,s2] == 0
                    for n in N for s2 in S if s2>0), "MaxConsFree")
            m.addConstrs(( tfs[n,s1,s2] <= tfs[n,s1-1,s2-1]
                    for n in N for s1 in S for s2 in S if s1>0 if s2>0), "MaxConsFree")
            m.addConstrs(( tfs[n,s1,s2] <= 1-q[n,s1]
                    for n in N for s1 in S for s2 in S if s1>0 if s2>0), "MaxConsFree")
            m.addConstrs(( tfs[n,s1,s2] >= tfs[n,s1-1,s2-1]-q[n,s1]
                    for n in N for s1 in S for s2 in S if s1>0 if s2>0), "MaxConsFree")
            if bounds[7,3]>0:
                m.addConstr(
                        (quicksum(tfs[n,s1,s2] for n in N for s1 in S for s2 in range(bounds[7,3],len(S)))==0),"maxconsfree"
                        )
            
            if bounds[7,2]>0:
                m.addConstrs(( sfs[n,0,s2] == 0
                        for n in N for s2 in S), "MinConsFree")
                m.addConstrs(( sfs[n,s1,s2] <= tfs[n,s1-1,s2]
                        for n in N for s1 in S for s2 in S if s1>0), "MinConsFree")
                m.addConstrs(( sfs[n,s1,s2] <= q[n,s1]
                        for n in N for s1 in S for s2 in S if s1>0), "MinConsFree")
                m.addConstrs(( sfs[n,s1,s2] >= tfs[n,s1-1,s2]+q[n,s1]-1
                        for n in N for s1 in S for s2 in S if s1>0), "MinConsFree")
                
                m.addConstrs(( sfs[n,num_shifts,s2] == tfs[n,num_shifts-1,s2]
                        for n in N for s2 in S), "MinConsWork")
                
                m.addConstr(
                        (quicksum(sfs[n,s1,s2]*(bounds[7,2]-1-s2) for n in N for s1 in Ss for s2 in range(bounds[7,2]-1))==0),"minconsfree"
                        )
                
        if bounds[11,5]+bounds[11,4]>0:
            m.addConstrs(( tw1[n,0,s,0] == o[n,0,s] for n in N for s in S), "MaxConsSameShift")
            m.addConstrs(( tw1[n,d1+1,s,0] <= o[n,d1+1,s]
                    for s in S for n in N for d1 in D if d1<len(D)-1), "MaxConsSameShift")
            m.addConstrs(( tw1[n,d1+1,s,0] <= 1-o[n,d1,s]
                    for s in S for n in N for d1 in D if d1<len(D)-1), "MaxConsSameShift")
            m.addConstrs(( tw1[n,d1+1,s,0] >= o[n,d1+1,s]-o[n,d1,s]
                    for s in S for n in N for d1 in D if d1<len(D)-1), "MaxConsSameShift")
            
            m.addConstrs(( tw1[n,0,s,d2] == 0
                    for s in S for n in N for d2 in D if d2>0), "MaxConsSameShift")
            m.addConstrs(( tw1[n,d1,s,d2] <= tw1[n,d1-1,s,d2-1]
                    for s in S for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsSameShift")
            m.addConstrs(( tw1[n,d1,s,d2] <= o[n,d1,s]
                    for s in S for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsSameShift")
            m.addConstrs(( tw1[n,d1,s,d2] >= o[n,d1,s]+tw1[n,d1-1,s,d2-1]-1
                    for s in S for n in N for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsSameShift")
            if bounds[11,5]>0:
                m.addConstr(
                        (quicksum(tw1[n,d1,s,d2] for s in S for n in N for d1 in D for d2 in range(bounds[11,5],len(D)))==0),"maxconssameshift"
                        )
        
            if bounds[11,4]>0:
                m.addConstrs(( sw1[n,0,s,d2] == 0
                        for s in S for n in N for d2 in D), "MinConsSameShift")
                m.addConstrs(( sw1[n,d1,s,d2] <= tw1[n,d1-1,s,d2]
                        for s in S for n in N for d1 in D for d2 in D if d1>0), "MinConsSameShift")
                m.addConstrs(( sw1[n,d1,s,d2] <= 1-o[n,d1,s]
                        for s in S for n in N for d1 in D for d2 in D if d1>0), "MinConsSameShift")
                m.addConstrs(( sw1[n,d1,s,d2] >= tw1[n,d1-1,s,d2]-o[n,d1,s]
                        for s in S for n in N for d1 in D for d2 in D if d1>0), "MinConsSameShift")
                
                m.addConstrs(( sw1[n,num_days,s,d2] == tw1[n,num_days-1,s,d2]
                        for n in N for s in S for d2 in D), "MinConsWork")
                
                m.addConstr(
                        (quicksum(sw1[n,d1,s,d2]*(bounds[11,4]-1-d2) for s in S for n in N for d1 in Ds for d2 in range(bounds[11,4]-1))==0),"minconssameshift"
                        )
            
        if bounds[11,3] + bounds[11,2]>0:
            m.addConstrs(( tw1f[n,0,s,0] == 1-o[n,0,s] for n in N for s in S), "MaxConsFree")
            m.addConstrs(( tw1f[n,d1+1,s,0] <= o[n,d1,s]
                    for n in N for s in S for d1 in D if d1<len(D)-1), "MaxConsFree")
            m.addConstrs(( tw1f[n,d1+1,s,0] <= 1-o[n,d1+1,s]
                    for n in N for s in S for d1 in D if d1<len(D)-1), "MaxConsFree")
            m.addConstrs(( tw1f[n,d1+1,s,0] >= o[n,d1,s]-o[n,d1+1,s]
                    for n in N for s in S for d1 in D if d1<len(D)-1), "MaxConsFree")
            
            m.addConstrs(( tw1f[n,0,s,d2] == 0
                    for n in N for s in S for d2 in D if d2>0), "MaxConsFree")
            m.addConstrs(( tw1f[n,d1,s,d2] <= tw1f[n,d1-1,s,d2-1]
                    for n in N for s in S for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsFree")
            m.addConstrs(( tw1f[n,d1,s,d2] <= 1-o[n,d1,s]
                    for n in N for s in S for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsFree")
            m.addConstrs(( tw1f[n,d1,s,d2] >= tw1f[n,d1-1,s,d2-1]-o[n,d1,s]
                    for n in N for s in S for d1 in D for d2 in D if d1>0 if d2>0), "MaxConsFree")
            if bounds[11,3]>0:
                m.addConstr(
                        (quicksum(tw1f[n,d1,s,d2] for n in N for s in S for d1 in D for d2 in range(bounds[11,3],len(D)))==0),"maxconsfree"
                        )
            
            if bounds[11,2]>0:
                m.addConstrs(( sw1f[n,0,s,d2] == 0
                        for n in N for s in S for d2 in D), "MinConsw1free")
                m.addConstrs(( sw1f[n,d1,s,d2] <= tw1f[n,d1-1,s,d2]
                        for n in N for s in S for d1 in D for d2 in D if d1>0), "MinConsw1free")
                m.addConstrs(( sw1f[n,d1,s,d2] <= o[n,d1,s]
                        for n in N for s in S for d1 in D for d2 in D if d1>0), "MinConsw1free")
                m.addConstrs(( sw1f[n,d1,s,d2] >= tw1f[n,d1-1,s,d2]+o[n,d1,s]-1
                        for n in N for s in S for d1 in D for d2 in D if d1>0), "MinConsw1free")
                
                m.addConstrs(( sw1f[n,num_days,s,d2] == tw1f[n,num_days-1,s,d2]
                        for n in N for s in S for d2 in D), "MinConsWork")
                
                m.addConstr(
                        (quicksum(sw1f[n,d1,s,d2]*(bounds[11,2]-1-d2) for n in N for s in S for d1 in Ds for d2 in range(bounds[11,2]-1))==0),"minconsw1free"
                        )
        
        m.setParam(GRB.Param.PoolSolutions, numSam)
        m.setParam(GRB.Param.PoolSearchMode, 2)
        m.optimize()
        nSolutions = m.SolCount
        print('Number of solutions found: ' + str(nSolutions))
        if (m.status==GRB.Status.INFEASIBLE):
            m.computeIIS()
            print('\nThe following constraint(s) cannot be satisfied:')
            for c in m.getConstrs():
                if c.IISConstr:
                    print('%s' % c.constrName)
        if m.status==GRB.Status.OPTIMAL:
            m.write('m.sol')
        
        for i in range(nSolutions):
            m.setParam(GRB.Param.SolutionNumber,i)
            solution=m.getAttr('xn', o)
            tmp=np.zeros([num_nurses,num_days,num_shifts])
            for key in solution:
                tmp[key]=round(solution[key])
            tSample=np.swapaxes(np.swapaxes(tmp,0,1),1,2)
            tmp_sol=tmp.astype(np.int64)
                
            with open(os.path.join(directory, "sol"+str(i)+".csv") ,"w+") as my_csv:
                csvWriter = csv.writer(my_csv,delimiter=',')
                
                row=['']
                for j in range(num_days):
                    row.extend(['D'+str(j)]*num_shifts)
                csvWriter.writerow(row)
                
                row=[]
                for j in range(num_shifts):
                    row.extend(['S'+str(j)])
                csvWriter.writerow([''] + row*num_days)
                
                tmp_sol.astype(int)
                for j in range(num_nurses):
                    row=['N'+str(j)]
                    row.extend(tmp_sol[j].flatten())
                    csvWriter.writerow(row)
            
    except GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))
    
    except AttributeError:
        print('Encountered an attribute error')