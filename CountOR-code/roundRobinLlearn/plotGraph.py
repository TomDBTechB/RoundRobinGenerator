#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 15:42:02 2018

@author: mohit
"""

import matplotlib.pyplot as plt
import numpy as np
from os.path import expanduser
home = expanduser("~")
#import matplotlib.colors as colors
#import matplotlib.cm as cm
def plot(sam):
    directory=home+'/Documents/PhD/EJOR/COUNT/data/'+sam
    ax=np.zeros(4)
    y_prec=np.zeros(4)
    yerr_prec=np.zeros(4)
    y_recall=np.zeros(4)
    yerr_recall=np.zeros(4)
    times=np.zeros(4)
    times_err=np.zeros(4)
    i=0
    with open(directory+ "/results.csv") as f:
        d = {}
        next(f)    # skip first header line
        for line in f:
    #        print(line.split(','))
            nurses,numSam,numSol,prec,prec_err,rec, rec_err,time,time_err = line.split(',')
            ax[i]=float(numSol)
            y_prec[i] = float(prec)
            yerr_prec[i] = float(prec_err)
            y_recall[i] = float(rec)
            yerr_recall[i] = float(rec_err)
            times[i] = float(time)
            times_err[i] = float(time_err)
            i+=1
    #print(ax)
    print(y_recall)
    print(yerr_recall)
    #ax=ax[0:5]
    plt.figure(1)
    plt.style.use('ggplot')
    plt.plot(ax,y_recall)
    plt.fill_between(ax, y_recall - yerr_recall, y_recall + yerr_recall, linewidth=0, alpha=0.35)
    plt.xlabel('Number of Examples', fontsize=15)
    plt.ylabel('Recall', fontsize=15)
    plt.axis([0, 50, 0, 100])
    
    plt.figure(2)
    plt.style.use('ggplot')
    plt.plot(ax,times)
    plt.fill_between(ax, times - times_err, times + times_err, linewidth=0, alpha=0.35)
    plt.xlabel('Number of Examples', fontsize=15)
    plt.ylabel('Time Taken (in sec)', fontsize=15)
    plt.axis([0, 50, 0, 10])
    
    if sam[1]=='1':
        plt.figure(3)
        plt.style.use('ggplot')
        plt.plot(ax,y_prec)
        plt.fill_between(ax, y_prec - yerr_prec, y_prec + yerr_prec, linewidth=0, alpha=0.35)
        plt.xlabel('Number of Examples', fontsize=15)
        plt.ylabel('Precision', fontsize=15)
        plt.axis([0, 50, 0, 100])

tag="01"
plot(tag+"0")
plot(tag+"1")
plot(tag+"2")

directory=home+'/Documents/PhD/EJOR/COUNT/data'
plt.figure(1)
plt.legend(['Small','Medium','Large'], loc='lower right', prop={'size':12})
ax = plt.gca()
ax.set_facecolor('xkcd:white')
ax.grid(color='black', linestyle='-', linewidth=0.15)
plt.savefig(directory+'/recall_'+tag+'.png', bbox_inches='tight', pad_inches=0, dpi=120)
#plt.show()

plt.figure(2)
plt.legend(['Small','Medium','Large'], loc='upper left', prop={'size':12})
ax = plt.gca()
ax.set_facecolor('xkcd:white')
ax.grid(color='black', linestyle='-', linewidth=0.15)
plt.savefig(directory+'/time_'+tag+'.png', bbox_inches='tight', pad_inches=0, dpi=120)

if tag[1]=='1':
    plt.figure(3)
    plt.legend(['Small','Medium','Large'], loc=8, prop={'size':12})
    ax = plt.gca()
    ax.set_facecolor('xkcd:white')
    ax.grid(color='black', linestyle='-', linewidth=0.15)
    plt.savefig(directory+'/precision_'+tag+'.png', bbox_inches='tight', pad_inches=0, dpi=120)



plt.show()
























