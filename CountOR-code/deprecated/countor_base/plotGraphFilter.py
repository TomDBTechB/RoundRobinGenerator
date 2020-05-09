"""
Created on Tue Apr 17 15:42:02 2018
@author: mohit
"""
import matplotlib.pyplot as plt
import numpy as np
from os.path import expanduser
home = expanduser("~")
def plot(sam):
    directory=home+'/Documents/PhD/EJOR/COUNT/data/filterPref/'+sam
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
            BK,MT, HS,target,numSol,learned,learned_err = line.split(',')
            ax[i]=float(numSol)
            y_recall[i] = ((72-float(learned))*100)/(72-float(target))
            yerr_recall[i] = float(learned_err)
            i+=1
    plt.figure(1)
    plt.style.use('ggplot')
    plt.plot(ax,y_recall)
    plt.fill_between(ax, y_recall - yerr_recall, y_recall + yerr_recall, linewidth=0, alpha=0.35)
    plt.xlabel('Number of Examples', fontsize=15)
    plt.ylabel('Constraints Filtered %', fontsize=15)
    plt.axis([0, 50, 0, 100])
tag="00"
plot(tag+"0")
plot(tag+"1")
plot(tag+"2")
directory=home+'/Documents/PhD/EJOR/COUNT/data/filterPref'
plt.figure(1)
plt.legend(['Small','Medium','Large'], loc='lower right', prop={'size':12})
ax = plt.gca()
ax.set_facecolor('xkcd:white')
ax.grid(color='black', linestyle='-', linewidth=0.15)
plt.savefig(directory+'/filter_'+tag+'.png', bbox_inches='tight', pad_inches=0, dpi=120)
plt.show()