import os

import matplotlib.pyplot as plt
import pandas as pd

folder = "./data/2_8_1500/"

# TODO add plus and minus of standard deviation and shade the region
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
    plt.xticks([1,5,10,25,50,100])
    plt.title("Precision in function of the number of used examples")
    plt.xlabel("Number of used examples")
    plt.ylabel("Precision and std error")
    plt.fill_between(soln,prec-prec_err,prec+prec_err,linewidth=0,alpha=0.35)

    # plt.figure(2)
    # plt.style.use('ggplot')
    # plt.plot(soln, rec)
    # plt.xticks([1, 5, 10, 25, 50, 100])
    # plt.title("Recall in function of the number of used examples")
    # plt.xlabel("Number of used examples")
    # plt.ylabel("Recall and std error")
    # plt.fill_between(soln, rec-rec_err, rec+rec_err, linewidth=0, alpha=0.35)

    # plt.figure(0)
    # plt.style.use('ggplot')
    # plt.plot(soln, time)
    # plt.xticks([1, 5, 10, 25, 50, 100])
    # plt.title("Learning time in function of the number of used examples")
    # plt.xlabel("Number of used examples")
    # plt.ylabel("Time(s)")
    # plt.fill_between(soln, time - time_err, time + time_err, linewidth=0, alpha=0.35)


    plt.show()




plotstderr_graphs(folder)
