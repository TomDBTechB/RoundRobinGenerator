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
from countSport import simple_sampler as sampler

# region vars
numSam = 100  # int(sys.argv[1])
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

tbounds = np.zeros([num_constrType, num_constr])
# defines upper/lower bounds
tbounds[2, 0] = 4
tbounds[2, 1] = 6
tbounds[6, 2] = 1
tbounds[6, 3] = 7
tbounds[6, 4] = 2
tbounds[9, 0] = 1
tbounds[9, 1] = 2
tbounds[10, 1] = 1
tbounds[6, 0] = 9
tbounds[6, 1] = 16
tbounds[6, 5] = 8
tbounds = tbounds.astype(np.int64)


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

def generateSamples(numTeams, numSam,sampleDir):
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + " teams from Java api")
    start = time.clock()
    #
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

    return soln, result,csvWriter,detCsvWriter,det_csv,my_csv


def resampleAndLearn():
    pass


# endregion


# Build directory structure for results and open up the files
directory = os.path.join(os.getcwd(), "data", tag)
soln, result,csvWriter,detCsvWriter,detcsv,mycsv = buildSolutionAndResultDirs(directory)

# generate the samples
generateSamples(numTeams, numSam,soln)

# learn the constraints
timeTaken = learnConstraints()

tag = "Amt_T" + str(numTeams)
file = os.path.join(directory,"results","learnedBounds","_" + tag + "0.csv")
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
        if numSol != 1:
            selRows = selectedRows[seed] + random.sample([x for x in range(0, numSam) if x not in selectedRows[seed]],
                                                         numSol - prevSol)
        else:
            selRows = random.sample(range(0,numSam),numSol)
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

            tmpDir = os.path.join(directory ,"tmp")
            cU.buildDirectory(tmpDir)
            cU.removeCSVFiles(tmpDir)

            soln = os.path.join(tmpDir ,"solutions")
            cU.buildDirectory(soln)
            cU.removeCSVFiles(soln)

            result = os.path.join(tmpDir + "results")
            cU.buildDirectory(result)
            cU.removeCSVFiles(result)

            print("\nGenerating samples using learned constraints")
            start = time.clock()
            sampler.generateSample(numTeams, num_Matchdays, numSam, bounds_learned,soln)
            print("Generated ", numSam, " samples in ", time.clock() - start, ' secs')

            prefSatisfaction = countor.learnConstraintsForAll(tmpDir, numTeams)
            tag = "Amt_T" + str(numTeams)
            file = os.path.join(tmpDir ,"results" ,"learnedBounds", "_" + tag + "0.csv")
            tmpBounds = sU.readBounds(file, num_constrType, num_constr)
            for i in range(len(tmpBounds)):
                accept = 0
                if mt == 0:
                    accept = sU.moreConstrained(tbounds, tmpBounds[i], num_constrType, num_constr)
                precision += accept
            tot_pre[seed] = (precision * 100) / numSam

            prec_prev = tot_pre[seed]
            rec_prev = tot_rec[seed]
            time_prev = tot_time[seed]
            bounds_prev = bounds_learned

        row =[]
        row.extend([numTeams])
        row.extend([numSol])
        row.extend([seed])
        row.extend([tot_pre[seed]])
        row.extend([tot_rec[seed]])
        print(row)
        detCsvWriter.writerow(row)

    prevSol = numSol
    row = []
    row.extend([numTeams])
    row.extend([numSam])
    row.extend([numSol])
    row.extend([sum(tot_pre) / numSeed])
    row.extend([np.std(tot_pre) / np.sqrt(numSeed)])
    row.extend([sum(tot_rec) / numSeed])
    row.extend([np.std(tot_rec) / np.sqrt(numSeed)])
    row.extend([sum(tot_time) / numSeed])
    row.extend([np.std(tot_time) / np.sqrt(numSeed)])
    csvWriter.writerow(row)
    print(row)

detcsv.close()
mycsv.close()
