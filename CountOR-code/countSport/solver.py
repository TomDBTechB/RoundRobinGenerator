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
numSam = 10  # int(sys.argv[1])
numTeams = 6  # int(sys.argv[2])
mt = 1  # int(sys.argv[3])
num_Matchdays = sU.calculateMatchDays(numTeams)
solution_seed = [1, 10, 25, 50]
tag = str(numTeams) + "_" + str(numSam)
num_constrType = 12  # maximum
num_constr = 6
# provides list of constraints
constrList = [[(0,), (1,)], [(0,), (2,)], [(0,), (1, 2)], [(1,), (0,)], [(1,), (2,)], [(1,), (0, 2)], [(2,), (0,)],
              [(2,), (1,)], [(2,), (0, 1)], [(0, 1), (2,)], [(0, 2), (1,)], [(1, 2), (0,)]]
constrMaxval = []
dimSize = [num_Matchdays, numTeams, numTeams]
for val in constrList:
    tot = 1
    for i in range(len(val[1])):
        tot *= dimSize[int(val[1][i])]
    constrMaxval.append(tot)
print(constrMaxval)


# endregion

# region structural methods

def generateSamples(numTeams, numSam):
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + " teams from Java api")
    start = time.clock()
    #
    sampleDir = os.path.join(os.getcwd(), "samples")
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    args = [os.path.join(os.getcwd(), "static", "SportScheduleGenerator.jar"), str(numTeams), str(numSam),
            sampleDir]  # Any number of args to be passed to the jar file
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

    return soln, result


def resampleAndLearn():
    pass


# endregion


# Build directory structure for results and open up the files
directory = os.path.join(os.getcwd(), "data", tag)
soln, result = buildSolutionAndResultDirs(directory)

# generate the samples
generateSamples(numTeams, numSam)

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
    tot_rec = np.zeros(numSeed)  # recall
    tot_pre = np.zeros(numSeed)  # precision
    tot_fn = np.zeros(numSeed)  # false negatives
    tot_fp = np.zeros(numSeed)  # false positives
    tot_time = np.zeros(numSeed)  # time to compute

    for seed in range(numSeed):
        recall, precision = 0, 0
        random.seed(seed)

        selRows = selectedRows[seed] + random.sample([x for x in range(0, numSam) if x not in selectedRows[seed]],
                                                     numSol - prevSol)
        selectedRows[seed] = selRows
        selbounds = np.array([lbounds[i] for i in selRows])
        start = time.clock()
        bounds_learned = sU.aggrBounds(selbounds, num_constrType, num_constr, constrMaxval)
        tot_time[seed] = ((timeTaken * numSol) / numSam) + (time.clock() - start)

        if (not (np.array_equal(bounds_learned, bounds_prev))):
            selbounds = np.array([lbounds[i] for i in range(len(lbounds)) if i not in selRows])
            for i in range(len(selbounds)):
                accept = sU.moreConstrained(bounds_learned, selbounds[i], num_constrType, num_constr)
                recall += accept
            tot_rec[seed] = (recall * 100) / (numSam - numSol)

            tmpDir = directory + "/tmp"
            cU.buildDirectory(tmpDir)
            cU.removeCSVFiles(tmpDir)

            soln = directory + "/solutions"
            cU.buildDirectory(soln)
            cU.removeCSVFiles(soln)
            result = directory + "/results"
            cU.buildDirectory(result)
            cU.removeCSVFiles(result)

            print("\nGenerating samples using learned constraints")
            start = time.clock()
            sampler.generateSample(num_nurses, num_days, num_shifts, numSam, extraConstPerc, nurse_skill,
                                   nurse_preference, bounds_learned, bounds_learned0, bounds_learned1,
                                   tmpDir + "/solutions", bk, 0)
            print("Generated ", numSam, " samples in ", time.clock() - start, ' secs')

            prefSatisfaction = countor.learnConstraintsForAll(tmpDir, num_nurses, nurse_skill, bk, 0, hs, 1,
                                                              nurse_preference)
            tag = str(bk) + str(0) + str(hs)
            file = tmpDir + "/results" + "/learnedBounds" + "_" + tag + "0.csv"
            tmpBounds = readBounds(file, num_constrType, num_constr)
            if bk == 1:
                file = tmpDir + "/results" + "/learnedBounds" + "_" + tag + "00.csv"
                tmpBounds0 = readBounds(file, num_constrType, num_constr)

                file = tmpDir + "/results" + "/learnedBounds" + "_" + tag + "01.csv"
                tmpBounds1 = readBounds(file, num_constrType, num_constr)

            for i in range(len(tmpBounds)):
                accept = 0
                if mt == 0 or prefSatisfaction[i] == 1:
                    accept = moreConstrained(tbounds, tmpBounds[i], num_constrType, num_constr)
                    if accept == 0 and bk == 1:
                        accept = moreConstrained(tbounds0, tmpBounds0[i], num_constrType, num_constr)
                        if accept == 0:
                            accept = moreConstrained(tbounds1, tmpBounds1[i], num_constrType, num_constr)
                precision += accept
            tot_pre[seed] = (precision * 100) / numSam

            prec_prev = tot_pre[seed]
            rec_prev = tot_rec[seed]
            time_prev = tot_time[seed]
            bounds_prev = bounds_learned
            bounds_prev0 = bounds_learned0
            bounds_prev1 = bounds_learned1
