"""entry point: the solver tries to solve the sport scheduling proble,"""
import glob
import os
import random
import sys
import time

import numpy as np

from countSport import solverUtils as sU
from countSport import countor


# region vars
numSam = 1 # int(sys.argv[1])
numTeams = 6 # int(sys.argv[2])
solution_seed = [1] # [1,10,25,50]
tag = str(numTeams)+"_"+str(numSam)
# TODO ask
num_constrType = 12
num_constr = 6
# endregion

# region structural methods

def generateSamples():
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + " from Java api")
    start = time.clock()
    # TODO pull this from a port or make it in a sampler.py file
    print("Generated ", numSam, " samples in ", time.clock() - start, " secs")

def learnConstraints():
    for fl in glob.glob(result + "/*.csv"):
        os.remove(fl)

    start = time.clock()
    countor.learnConstraintsForAll(directory, numTeams)
    timeTaken = time.clock() - start
    print("\nLearned bounds for ", numSam, " samples in ", timeTaken, ' secs')
    return timeTaken

# endregion



# Build directory structure for results and open up the files
directory = os.getcwd() + '/data/' + tag
if not os.path.exists(directory):
    os.makedirs(directory)
my_csv, csvWriter = sU.openMainCsv(directory)
det_csv, detCsvWriter = sU.openDetCsv(directory)

soln = os.path.join(directory ,"solutions")
result = os.path.join(directory,"results","learnedBounds")

if not os.path.exists(soln):
    os.makedirs(soln)
if not os.path.exists(result):
    os.makedirs(result)

# generate the samples
generateSamples()

# learn the constraints
timeTaken = learnConstraints()


tag = "Amt_T" + str(numTeams)
file = result + "/learnedBounds" + "_" + tag + "0.csv"
lbounds = sU.readBounds(file, num_constrType, num_constr)
bounds_prev = np.zeros([num_constrType, num_constr])
bounds_prev0 = np.zeros([num_constrType, num_constr])
bounds_prev1 = np.zeros([num_constrType, num_constr])
prec_prev = 0
rec_prev = 0
time_prev = 0

prevSol = 0
numSeed = len(solution_seed)
selectedRows = [[] for _ in range(numSeed)]
for numSol in solution_seed:
    print("\n############ Number of examples used: ", numSol, " ############")
    tot_rec = np.zeros(numSeed) # recall
    tot_pre = np.zeros(numSeed) # precision
    tot_fn = np.zeros(numSeed)  # false negatives
    tot_fp = np.zeros(numSeed)  # false positives
    tot_time = np.zeros(numSeed)# time to compute

    for seed in range(numSeed):
        recall,precision = 0,0
        random.seed(seed)

        selRows = selectedRows[seed] + random.sample([x for x in range(0, numSam) if x not in selectedRows[seed]],
                                                     numSol - prevSol)
        selectedRows[seed] = selRows
        selbounds = np.array([lbounds[i] for i in selRows])
        start = time.clock()
        bounds_learned = sU.aggrBounds(selbounds, num_constrType, num_constr, constrMaxval)
        tot_time[seed] = ((timeTaken * numSol) / numSam) + (time.clock() - start)
        learned_cc = np.count_nonzero(bounds_learned)
        bounds_learned0 = np.zeros([num_constrType, num_constr])


