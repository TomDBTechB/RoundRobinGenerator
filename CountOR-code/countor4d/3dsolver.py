"""entry point: the solver tries to solve the sport scheduling proble,"""
import glob
import os
import random
import shutil
import time

import numpy as np

from countor4d import countor
from countor4d import countorUtils as cU
from countor4d import simple_sampler as sampler
from countor4d import solverUtils as sU

# region vars

numSam = 100  # int(sys.argv[1])
numTeams = 6  # int(sys.argv[2])
num_Matchdays = sU.calculateMatchDays(numTeams)
solution_seed = [1, 10, 25, 50]
tag = str(numTeams) + "_" + str(numSam)
num_constrType = 12  # maximum
num_constr = 6
# provides list of constraints
# 0 is rounds, 1 is away, 2 is home
constrList = [[(0,), (1,)], [(0,), (2,)], [(0,), (1, 2)], [(1,), (0,)], [(1,), (2,)], [(1,), (0, 2)], [(2,), (0,)],
              [(2,), (1,)], [(2,), (0, 1)], [(0, 1), (2,)], [(0, 2), (1,)], [(1, 2), (0,)]]


constrMaxval = []
dimSize = [num_Matchdays, numTeams, numTeams]
for val in constrList:
    tot = 1
    for i in range(len(val[1])):
        tot *= dimSize[int(val[1][i])]
    constrMaxval.append(tot)
# print(constrMaxval)

# endregion

# region structural methods


def checkmoreconstrained(bound, benchmarkbound):
    '''
    Checks whether the given bound is more constrained than the provided benchmarkbound
    :param bound:
    :param benchmarkbound: The benchmarkbound which should contain the lowest and highest bound
    :return:
    '''
    total = 0
    for i in range(len(bound)):
        for j in range(0,len(bound[i]),2):
            if(benchmarkbound[i][j] <= bound[i][j] and benchmarkbound[i][j+1] >= benchmarkbound[i][j]):
                total+=1
            else:
                pass
    recall_this_set = total / (len(bound)*len(benchmarkbound[0])/2)
    return recall_this_set


"""
Generates a numSam of solutions for the sport scheduling problem with numTeams teams and stores them in sampleDir
"""
def generateSamples(numTeams, numSam, sampleDir):
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + " teams from Java api")
    start = time.clock()
    #
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    args = [os.path.join(os.getcwd(), "static", "SportScheduleGenerator.jar"), str(numTeams), str(numSam),
            sampleDir]  # Any number of args to be passed to the jar file
    sU.jarWrapper(*args)
    print("Generated ", numSam, " samples in ", time.clock() - start, " secs")

def buildSolutionAndResultDirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    my_csv, csvWriter = sU.openMainCsv(directory)
    det_csv, detCsvWriter = sU.openDetCsv(directory)

    soln = os.path.join(directory, "solutions")
    result = os.path.join(directory, "results", "learnedBounds")
    prec = os.path.join(directory, "results", "validation")

    if not os.path.exists(soln):
        os.makedirs(soln)
    if not os.path.exists(result):
        os.makedirs(result)

    if not os.path.exists(prec):
        os.makedirs(prec)

    return soln, result, prec, csvWriter, detCsvWriter, det_csv, my_csv

def validateSamples(sampleDirectory):
    start = time.clock()

    args = [os.path.join(os.getcwd(), "static", "SportSchedulePrecisionCalculator.jar"),sampleDirectory]
    print(sU.jarWrapper(*args))
    print("Validated samples from a model of " + str(numSam) +" schedules in " + str(time.clock() - start))

def randomSplit(dir, learnsplit):
    path, dirs, files = next(os.walk(dir))
    cU.buildDirectory(os.path.join(dir, "learn"))
    cU.buildDirectory(os.path.join(dir, "test"))
    for file in range(0, len(files)):
        if random.uniform(0, 1) < learnsplit:
            shutil.move(os.path.join(dir, files[file]), os.path.join(dir, "learn", files[file]))
        else:
            shutil.move(os.path.join(dir, files[file]), os.path.join(dir, "test", files[file]))

def learnConstraintsFromFiles(learndir, sampled_files, outputdir):
    for fl in glob.glob(result + "/*.csv"):
        os.remove(fl)

    start = time.clock()
    countor.learnConstraintsForAll(learndir, sampled_files, numTeams, outputdir)
    timeTaken = time.process_time() - start
    print("\nLearned bounds for ", len(sampled_files), " samples in ", timeTaken, ' secs')
    return timeTaken


def calculateRecallFromFile(file, testsolndir):
    '''
    Calculates the recall from a given bounds file and compares it to the bounds learned from a complete set of test solutions
    :param file:
    :param testsolndir:
    :return:
    '''
    learned_bounds = sU.read3dBounds(file, num_constrType, num_constr)
    aggregated_learned_bounds = sU.aggrBounds(selbounds=learned_bounds,num_constr=num_constr,num_constrType=num_constrType,constrMaxval=constrMaxval)
    files = next(os.walk(testsolndir))[2]
    learnConstraintsFromFiles(testsolndir, files, prec)
    file = os.path.join(directory, "results", "validation",
                        "_" + str(len(files)) + "Amt_T" + str(numTeams) + "0.csv")
    recallBounds = sU.readBounds(file, num_constrType, num_constr)

    accept = 0
    for i in recallBounds:
        accept += checkmoreconstrained(bound=i, benchmarkbound=aggregated_learned_bounds)
    return accept / len(recallBounds)

# endregion


# Build directory structure for results and open up the files
directory = os.path.join(os.getcwd(), "3Ddata", tag)
soln, result, prec, csvWriter, detCsvWriter, detcsv, mycsv = buildSolutionAndResultDirs(directory)

# generate the samples
generateSamples(numTeams, numSam, soln)
#split into 0.8 learn 0.2 testset
randomSplit(soln, 0.8)


for numSol in solution_seed:
    # grab numSol from the learning set of schedules
    learndir = os.path.join(soln, "learn")
    path, dirs, files = next(os.walk(learndir))
    sampled_files = random.sample(files, numSol)

    # learn the combined model from the java schedules and store it in results/learnedBounds
    timeTaken = learnConstraintsFromFiles(learndir, sampled_files, result)
    print("Learned Constraints from " + str(numSol) + " Java schedules in " + str(timeTaken) + "ms")
    tag = str(numSol) + "Amt_T" + str(numTeams)
    file = os.path.join(directory, "results", "learnedBounds", "_" + tag + "0.csv")
    lbounds = sU.read3dBounds(file, num_constrType, num_constr)
    aggr_bounds = sU.aggrBounds(selbounds=lbounds,num_constrType=num_constrType,num_constr=num_constr,constrMaxval=constrMaxval)
    tmpDir = os.path.join(directory,"tmp")
    cU.buildDirectory(tmpDir)
    cU.removeCSVFiles(tmpDir)

    # build numSam samples from the learned constraints
    sampler.generateSample(num_teams=numTeams, num_matchdays=num_Matchdays, numSam=500, bounds=aggr_bounds,
                           directory=tmpDir)


    validateSamples(sampleDirectory=tmpDir)

    recall = calculateRecallFromFile(file=file, testsolndir=os.path.join(soln, "test"))
    print("recall: " + str(recall))



detcsv.close()
mycsv.close()

