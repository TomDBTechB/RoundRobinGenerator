"""entry point: the solver tries to solve the sport scheduling proble,"""
import glob
import os
import random
import shutil
import time

import numpy as np

from countSport import countor
from countSport import countorUtils as cU
from countSport import simple_sampler as sampler
from countSport import solverUtils as sU

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
constrValues = [[(3, 3)], [(3, 3)], [(3, 3)], [(5, 5)], [(5, 5)], [(5, 5)], [(5, 5)], [(5, 5)], [(5, 5)], [(0, 1)],
                [(0, 1)], [(0, 1)]]



# endregion

# region structural methods


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
    cU.removeCSVFiles(soln)
    cU.removeCSVFiles(result)
    cU.removeCSVFiles(prec)

    return soln, result, prec, csvWriter, detCsvWriter, det_csv, my_csv


def randomSplit(dir, learnsplit):
    path, dirs, files = next(os.walk(dir))
    cU.buildDirectory(os.path.join(dir, "learn"))
    cU.removeCSVFiles(os.path.join(dir,"learn"))
    cU.buildDirectory(os.path.join(dir, "test"))
    cU.removeCSVFiles(os.path.join(dir,"test"))
    for file in range(0, len(files)):
        if random.uniform(0, 1) < learnsplit:
            shutil.move(os.path.join(dir, files[file]), os.path.join(dir, "learn", files[file]))
        else:
            shutil.move(os.path.join(dir, files[file]), os.path.join(dir, "test", files[file]))


def learnConstraintsFromFiles(learndir, sampled_files, outputdir):


    start = time.clock()
    countor.learnConstraintsForAll(learndir, sampled_files, numTeams, outputdir)
    timeTaken = time.process_time() - start
    print("\nLearned bounds for ", len(sampled_files), " samples in ", timeTaken, ' secs')
    return timeTaken


def calculatePrecisionFromSampleDir(numSol, sampledir):
    args = [os.path.join(os.getcwd(), "static", "SportSchedulePrecisionCalculator.jar"), sampledir]
    print(sU.jarWrapper(*args))
    print("Done calculating precision for " + str(numSol))


def calculateRecallFromFile(numSol, file, testsolndir, tag):
    learned_bounds = sU.readBounds(file, num_constrType, num_constr)

    files = next(os.walk(testsolndir))[2]
    learnConstraintsFromFiles(testsolndir, files, prec)
    file = os.path.join(directory, "results", "validation",
                        "_" + str(len(files)) + "Amt_T" + str(numTeams) + "0.csv")
    recallBounds = sU.readBounds(file, num_constrType, num_constr)

    accept = 0
    for i in recallBounds:
       accept += moreConstrained(i,learned_bounds)
    return accept/len(recallBounds)


def checkmoreconstrained(bound, benchmarkbound):
    for i in range(len(bound)-1):
        if(benchmarkbound[i] <= bound[i] and benchmarkbound[i+1] >= bound[i+1]):
            pass
        else:
            return False
    return True


def moreConstrained(recall_bound,model_bounds):
    for model_bound in model_bounds:
        if not checkmoreconstrained(bound=recall_bound[0],benchmarkbound=model_bound[0]):
            return 0
    return 1




# endregion


# Build directory structure for results and open up the files
directory = os.path.join(os.getcwd(), "data", tag)
soln, result, prec, csvWriter, detCsvWriter, detcsv, mycsv = buildSolutionAndResultDirs(directory)

# generate the samples
generateSamples(numTeams, numSam, soln)
# split into 0.8 learn 0.2 testset
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
    lbounds = sU.readBounds(file, num_constrType, num_constr)

    tmpDir = os.path.join(directory, "tmp")
    cU.buildDirectory(tmpDir)
    cU.removeCSVFiles(tmpDir)

    # build numSam samples from the learned constraints
    sampler.generateSample(num_teams=numTeams, num_matchdays=num_Matchdays, numSam=500, bounds=lbounds[0],
                           directory=tmpDir)

    calculatePrecisionFromSampleDir(sampledir=tmpDir, numSol=500)
    recall = calculateRecallFromFile(numSol=numSol, file=file, testsolndir=os.path.join(soln, "test"), tag=tag)

    row = []
    row.extend([numTeams])
    row.extend([numSam])
    row.extend([numSol])
    row.extend([1.0])
    row.extend([recall])

    detCsvWriter.writerow(row)

detcsv.close()
mycsv.close()
