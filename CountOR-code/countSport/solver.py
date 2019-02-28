"""entry point: the solver tries to solve the sport scheduling proble,"""
import glob
import os
import random
import sys
import time

import numpy as np

from countSport import solverUtils as sU
from countSport import countorUtils as cU
from countSport import countor


# region vars
numSam = 1 # int(sys.argv[1])
numTeams = 6 # int(sys.argv[2])
mt = 1 # int(sys.argv[3])
# todo extract this
num_Matchdays = 12
num_matches = 3
solution_seed = [1] # [1,10,25,50]
tag = str(numTeams)+"_"+str(numSam)
# TODO ask
num_constrType = 12 # maximum
num_constr = 6
# provides list of constraints
constrList = [[(0,), (1,)], [(0,), (2,)], [(0,), (1, 2)], [(1,), (0,)], [(1,), (2,)], [(1,), (0, 2)], [(2,), (0,)],
              [(2,), (1,)], [(2,), (0, 1)], [(0, 1), (2,)], [(0, 2), (1,)], [(1, 2), (0,)]]
constrMaxval = []
dimSize = [num_Matchdays, numTeams, num_matches]
for val in constrList:
    tot = 1
    for i in range(len(val[1])):
        tot *= dimSize[int(val[1][i])]
    constrMaxval.append(tot)
print(constrMaxval)
# endregion

# region structural methods

def generateSamples(numTeams,numSam):
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + " teams from Java api")
    start = time.clock()
    #
    sampleDir = os.path.join(os.getcwd(),"samples")
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    args = [os.path.join(os.getcwd(),"static","SportScheduleGenerator.jar"),str(numTeams), str(numSam), sampleDir] # Any number of args to be passed to the jar file
    print(sU.jarWrapper(*args))
    print("Generated ", numSam, " samples in ", time.clock() - start, " secs")

def learnConstraints():
    for fl in glob.glob(result + "/*.csv"):
        os.remove(fl)

    start = time.clock()
    countor.learnConstraintsForAll(directory, numTeams)
    timeTaken = time.clock() - start
    print("\nLearned bounds for ", numSam, " samples in ", timeTaken, ' secs')
    return timeTaken

def buildSolutionAndResultDirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    my_csv, csvWriter = sU.openMainCsv(directory)
    det_csv, detCsvWriter = sU.openDetCsv(directory)

    soln = os.path.join(directory, "solutions")
    result = os.path.join(directory, "results", "learnedBounds")

    if not os.path.exists(soln):
        os.makedirs(soln)
    if not os.path.exists(result):
        os.makedirs(result)

    return soln,result

def resampleAndLearn():
    pass

# endregion



# Build directory structure for results and open up the files
directory = os.path.join(os.getcwd(), "data",tag)
soln,result = buildSolutionAndResultDirs(directory)

# generate the samples
generateSamples(numTeams,numSam)

# learn the constraints
timeTaken = learnConstraints()


# tag = "Amt_T" + str(numTeams)
# file = result + "/learnedBounds" + "_" + tag + "0.csv"
# lbounds = sU.readBounds(file, num_constrType, num_constr)
# bounds_prev = np.zeros([num_constrType, num_constr])
# bounds_prev0 = np.zeros([num_constrType, num_constr])
# bounds_prev1 = np.zeros([num_constrType, num_constr])
# prec_prev = 0
# rec_prev = 0
# time_prev = 0
#
# prevSol = 0
# numSeed = len(solution_seed)
# selectedRows = [[] for _ in range(numSeed)]
# for numSol in solution_seed:
#     print("\n############ Number of examples used: ", numSol, " ############")
#     tot_rec = np.zeros(numSeed) # recall
#     tot_pre = np.zeros(numSeed) # precision
#     tot_fn = np.zeros(numSeed)  # false negatives
#     tot_fp = np.zeros(numSeed)  # false positives
#     tot_time = np.zeros(numSeed)# time to compute
#
#     for seed in range(numSeed):
#         recall,precision = 0,0
#         random.seed(seed)
#
#         selRows = selectedRows[seed] + random.sample([x for x in range(0, numSam) if x not in selectedRows[seed]],
#                                                      numSol - prevSol)
#         selectedRows[seed] = selRows
#         selbounds = np.array([lbounds[i] for i in selRows])
#         start = time.clock()
#         bounds_learned = sU.aggrBounds(selbounds, num_constrType, num_constr, constrMaxval)
#         tot_time[seed] = ((timeTaken * numSol) / numSam) + (time.clock() - start)
#         learned_cc = np.count_nonzero(bounds_learned)
#         # lower bounds?
#         bounds_learned0 = np.zeros([num_constrType, num_constr])
#         # upper bounds?
#         bounds_learned1 = np.zeros([num_constrType, num_constr])
#
#         if (mt == 1 and not (np.array_equal(bounds_learned, bounds_prev)
#                              and np.array_equal(bounds_learned0,bounds_prev0)
#                              and np.array_equal(bounds_learned1, bounds_prev1))) \
#             or (mt == 0 and not (np.array_equal(bounds_learned, bounds_prev))):
#                 selbounds = np.array([lbounds[i] for i in range(len(lbounds)) if i not in selRows])
#                 selbounds0 = np.array([lbounds0[i] for i in range(len(lbounds0)) if i not in selRows])
#                 selbounds1 = np.array([lbounds1[i] for i in range(len(lbounds1)) if i not in selRows])
#                 for i in range(len(selbounds)):
#                     accept = sU.moreConstrained(bounds_learned, selbounds[i], num_constrType, num_constr)
#                     if accept == 0:
#                         accept = sU.moreConstrained(bounds_learned0, selbounds0[i], num_constrType, num_constr)
#                         if accept == 0:
#                             accept = sU.moreConstrained(bounds_learned1, selbounds1[i], num_constrType, num_constr)
#                     recall += accept
#                 tot_rec[seed] = (recall * 100) / (numSam - numSol)
#
#                 tmpDir = directory + "/tmp"
#                 if not os.path.exists(tmpDir):
#                     os.makedirs(tmpDir)
#                 for fl in glob.glob(tmpDir + "/*.csv"):
#                     os.remove(fl)
#
#                 soln = directory + "/solutions"
#                 result = directory + "/results"
#
#                 if not os.path.exists(tmpDir + "/solutions"):
#                     os.makedirs(tmpDir + "/solutions")
#                 for fl in glob.glob(tmpDir + "/solutions" + "/*.csv"):
#                     os.remove(fl)
#                 if not os.path.exists(tmpDir + "/results"):
#                     os.makedirs(tmpDir + "/results")
#                 for fl in glob.glob(tmpDir + "/results" + "/*.csv"):
#                     os.remove(fl)
#
#
#

