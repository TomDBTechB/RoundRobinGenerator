import os

import matplotlib.pyplot as plt
import pandas as pd

folder = "./Thesis_data/4_8_1500_countor4d/"

# axis labels on everything
# TURN ON GRIDLINES AND CHANGE the x axis ticks

def plotstderr_graphs(folder):
    df = pd.read_csv(os.path.join(folder,"results.csv"))
    soln = df['Soln']
    prec = df['Precision']
    prec_err = df['Precision_err']
    rec = df['Recall']
    rec_err = df['Recall_err']
    time = df['Time']
    time_err = df['Time_err']

    plt.figure(1)
    plt.style.use('ggplot')
    plt.plot(soln,prec)
    plt.xticks([1,5,10,25,50])
    plt.title("Precision in function of the number of used examples")
    plt.xlabel("Number of used examples")
    plt.ylabel("Precision and std error")
    plt.fill_between(soln,prec-prec_err,prec+prec_err,linewidth=0,alpha=0.35)
    plt.savefig(os.path.join(folder,'precision.png'))

    plt.figure(2)
    plt.style.use('ggplot')
    plt.plot(soln, rec)
    plt.xticks([1, 5, 10, 25, 50])
    plt.title("Recall in function of the number of used examples")
    plt.xlabel("Number of used examples")
    plt.ylabel("Recall and std error")
    plt.fill_between(soln, rec-rec_err, rec+rec_err, linewidth=0, alpha=0.35)
    plt.savefig(os.path.join(folder,'recall.png'))

    plt.figure(3)
    plt.style.use('ggplot')
    plt.plot(soln, time)
    plt.xticks([1, 5, 10, 25, 50])
    plt.title("Learning time in function of the number of used examples")
    plt.xlabel("Number of used examples")
    plt.ylabel("Time(s)")
    plt.fill_between(soln, time - time_err, time + time_err, linewidth=0, alpha=0.35)
    plt.savefig(os.path.join(folder,'time.png'))







plotstderr_graphs(folder)
