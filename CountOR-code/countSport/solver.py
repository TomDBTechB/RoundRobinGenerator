"""entry point: the solver tries to solve the sport scheduling proble,"""
import os
import random
import shutil
import time

import numpy as np

from countSport import countor
from countSport import countorUtils as cU
from countSport import multi_dimensional_sampler as sampler
from countSport import solverUtils as sU


def calculatePrecisionNonBounds(sampledir):
    files = next(os.walk(sampledir))[2]
    accept, checks = 0, 0
    for file in files:
        path = os.path.join(sampledir, file)
        data = cU.readCSV(path)
        data_tensor = cU.cleanData(data)[0]
        for c in range(len(data_tensor)):
            for d in range(len(data_tensor[0])):
                trace = 0
                games_played = 0
                for i in range(len(data_tensor[0][0])):
                    trace += data_tensor[c][d][i][i]
                    games_played += sum(data_tensor[c][d][:][i])
                    games_played += sum(data_tensor[c][d][i][:])

                if trace == 0:
                    accept += 1
                if games_played <= 1:
                    accept += 1
                checks += 2
    return accept / checks




# region vars
numSam = 100  # int(sys.argv[1])
numTeams = 8  # int(sys.argv[2])
numCycle = 2
num_Matchdays = sU.calculateMatchDaysPerCycle(numTeams)
solution_seed = [1, 5, 10, 25, 50, 100]
tag = str(numCycle) + "_" + str(numTeams) + "_" + str(numSam)
# provides list of constraints
# 0 is cycles, 1 is rounds, 2 is away, 3 is home
constrList = [[(0,), (1,)], [(0,), (2,)], [(0,), (3,)], [(0,), (1, 2)], [(0,), (1, 3)], [(0,), (2, 3)],
              [(0,), (1, 2, 3)],
              [(1,), (0,)], [(1,), (2,)], [(1,), (3,)], [(1,), (0, 2)], [(1,), (0, 3)], [(1,), (2, 3)],
              [(1,), (0, 2, 3)],
              [(2,), (0,)], [(2,), (1,)], [(2,), (3,)], [(2,), (0, 1)], [(2,), (0, 3)], [(2,), (1, 3)],
              [(2,), (0, 1, 3)],
              [(3,), (0,)], [(3,), (1,)], [(3,), (2,)], [(3,), (0, 1)], [(3,), (0, 2)], [(3,), (1, 2)],
              [(3,), (0, 1, 2)],
              [(0, 1), (2,)], [(0, 1), (3,)], [(0, 1), (2, 3)],
              [(0, 2), (1,)], [(0, 2), (3,)], [(0, 2), (1, 3)],
              [(0, 3), (1,)], [(0, 3), (2,)], [(0, 3), (1, 2)],
              [(1, 2), (0,)], [(1, 2), (3,)], [(1, 2), (0, 3)],
              [(1, 3), (0,)], [(1, 3), (2,)], [(1, 3), (0, 2)],
              [(2, 3), (0,)], [(2, 3), (1,)], [(2, 3), (0, 1)],
              [(0, 1, 2), (3,)],
              [(0, 1, 3), (2,)],
              [(0, 2, 3), (1,)],
              [(1, 2, 3), (0,)]]

num_constrType = len(constrList)
# number of constraint values we capture: minCount, maxCount, minConsZero, maxConsZero, minConsOne, maxConsOne
num_constr = 6

actual_model_bounds = np.zeros([num_constrType, num_constr])
model_bounds = sU.calculateBounds4D(amtTeams=numTeams, amtCycles=numCycle, actual_model_bounds=actual_model_bounds)

constrMaxval = []
dimSize = [numCycle, num_Matchdays, numTeams, numTeams]
for val in constrList:
    tot = 1
    for i in range(len(val[1])):
        tot *= dimSize[int(val[1][i])]
    constrMaxval.append(tot)
# endregion


# region structural methods


"""
Generates a numSam of solutions for the sport scheduling problem with numTeams teams and stores them in sampleDir
"""


def generate4DSamples(numTeams, numSam, numCycles, sampleDir, mbounds):
    '''
    Generates 4D samples of the SSP
    :param numTeams: Number of teams for the SSP
    :param numSam: Number of samples to generate
    :param numCycles: number of cycles in the ssp
    :param sampleDir: directory where the generated samples end up in
    :param mbounds:
    :return:
    '''
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + "teams and " + str(
        numCycle) + " cycles teams from Gurobi")
    start = time.clock()
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    sampler.generate_multi_dim_sample(bounds=mbounds, directory=sampleDir, num_teams=numTeams,
                                      num_md_per_cycle=sU.calculateMatchDaysPerCycle(numTeams), numSam=numSam,
                                      numCycle=numCycles, theoretical=True)
    print("Generated ", numSam, " samples in ", time.clock() - start, " secs")


def generateSamples(numTeams, numSam, numCycles, sampleDir):
    '''
    The java api sample generator
    :param numTeams:
    :param numSam:
    :param numCycles:
    :param sampleDir:
    :return:
    '''
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + " teams from Java api")
    start = time.clock()
    #
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    args = [os.path.join(os.getcwd(), "static", "SportScheduleGenerator.jar"), str(numTeams), str(numSam),
            str(numCycles),
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
    cU.removeCSVFiles(os.path.join(dir, "learn"))
    cU.buildDirectory(os.path.join(dir, "test"))
    cU.removeCSVFiles(os.path.join(dir, "test"))

    amt_files = len(files)
    amt_learnfiles = learnsplit * amt_files

    learnfiles = random.sample(files, int(amt_learnfiles))

    for file in learnfiles:
        shutil.move(os.path.join(dir, file), os.path.join(dir, "learn", file))
    for file in next(os.walk(dir))[2]:
        shutil.move(os.path.join(dir, file), os.path.join(dir, "test", file))


def learnConstraintsFromFiles(learndir, sampled_files, outputdir):
    start = time.clock()
    countor.learnConstraintsForAll(learndir, sampled_files, numTeams, outputdir)
    timeTaken = time.process_time() - start
    return timeTaken


def checkmoreconstrained(bound, benchmarkbound):
    '''
    Checks whether the given bound is more constrained than the provided benchmarkbound
    :param bound:
    :param benchmarkbound: The benchmarkbound which should contain the lowest and highest bound
    :return:
    '''
    total = 0
    for i in range(len(bound)):
        if (benchmarkbound[i] == np.zeros(len(bound[i]))).all():
            total += len(benchmarkbound[i]) / 2
            continue
        for j in range(0, len(bound[i]), 2):
            if (benchmarkbound[i][j] <= bound[i][j] and benchmarkbound[i][j + 1] >= benchmarkbound[i][j]):
                total += 1
            else:
                pass
    recall_this_set = total / (len(bound) * len(benchmarkbound[0]) / 2)
    return recall_this_set


def check_constrained(sampled_bound, model_bound):
    for i in range(sampled_bound.shape[0]):
        if (model_bounds[i] == np.zeros(len(sampled_bound[i]))).all():
            continue
        for j in range(0, sampled_bound[i].shape[0], 2):
            if (model_bound[i][j] <= sampled_bound[i][j] and model_bound[i][j + 1] >= sampled_bound[i][j + 1]):
                continue
            else:
                return 0
    return 1


def column(matrix, i):
    return [row[i] for row in matrix]

def check_non_bounds_constrained(file):
    data = cU.readCSV(file)
    data_tensor = cU.cleanData(data)[0]
    for c in range(len(data_tensor)):
        for d in range(len(data_tensor[0])):
            trace = 0
            for i in range(len(data_tensor[0][0])):
                trace += data_tensor[c][d][i][i]
                games_played = 0
                print(data_tensor[c][d][i])
                print(column(data_tensor[c][d],i))


                games_played += sum(data_tensor[c][d][i])
                games_played += sum(column(data_tensor[c][d],i))
                if games_played > 1:
                    return 0
            if trace != 0:
                return 0
    return 1


def calculatePrecisionCorrect(model_bounds, sampledir):
    files = next(os.walk(sampledir))[2]
    sample_bound_file = os.path.join(tmpResult, "_" + str(len(files)) + "Amt_T" + str(numTeams) + "0.csv")
    learnConstraintsFromFiles(sampledir, files, tmpResult)
    precisionBounds = sU.readBounds(sample_bound_file, num_constrType, num_constr)

    accept = 0
    for i in range(precisionBounds.shape[0]):
        boundsval = check_constrained(precisionBounds[i], model_bounds)
        non_bounds_val = check_non_bounds_constrained(os.path.join(sampledir, files[i]))
        if boundsval + non_bounds_val == 2:
            accept += 1
    return accept / len(files)


def calculatePrecisionFromSampleDir(model_bounds, sampledir):
    '''
    Calculates the precision over all the samples in the sampledir
    :param model_bounds: the tbounds provided by ourselves
    :param sampledir: the sample directory generated from the learned bounds of a seed
    :return:
    '''
    files = next(os.walk(sampledir))[2]
    sample_bound_file = os.path.join(tmpResult, "_" + str(len(files)) + "Amt_T" + str(numTeams) + "0.csv")
    learnConstraintsFromFiles(sampledir, files, tmpResult)
    precisionBounds = sU.readBounds(sample_bound_file, num_constrType, num_constr)

    accept = 0
    for i in precisionBounds:
        accept += checkmoreconstrained(bound=i, benchmarkbound=model_bounds)
    return accept / len(precisionBounds)


def calculateRecallFromFile(file, testsolndir):
    '''
    Calculates the recall from a given bounds file and compares it to the bounds learned from a complete set of test solutions
    :param file:
    :param testsolndir:
    :return:
    '''
    learned_bounds = sU.readBounds(file, num_constrType, num_constr)
    aggregated_learned_bounds = sU.aggrBounds(selbounds=learned_bounds, num_constr=num_constr,
                                              num_constrType=num_constrType, constrMaxval=constrMaxval)
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
directory = os.path.join(os.getcwd(), "data", tag)
soln, result, prec, csvWriter, detCsvWriter, detcsv, mycsv = buildSolutionAndResultDirs(directory)

# generate the samples
generate4DSamples(mbounds=model_bounds, numTeams=numTeams, numSam=numSam, numCycles=numCycle, sampleDir=soln)
# split into 0.8 learn 0.2 testset
randomSplit(soln, 0.9)

numSeed = len(solution_seed)

prev_seeds = [[] for _ in range(numSeed)]

for numSol in solution_seed:
    all_rec = np.zeros(numSeed)
    all_pre = np.zeros(numSeed)
    all_time = np.zeros(numSeed)

    for seed in range(numSeed):
        # set the seed for this run of the precisions
        random.seed(seed)
        # grab numSol from the learning set of schedules
        learndir = os.path.join(soln, "learn")
        path, dirs, files = next(os.walk(learndir))
        sampled_files = random.sample(files, numSol - len(prev_seeds[seed]))
        sampled_files += prev_seeds[seed]
        prev_seeds[seed] = sampled_files

        # learn the combined model from the java schedules and store it in results/learnedBounds
        timeTaken = learnConstraintsFromFiles(learndir, sampled_files, result)
        print(str(seed) + ": Learned bounds for ", len(sampled_files), " samples in ", timeTaken, ' secs \n')
        tag = str(numSol) + "Amt_T" + str(numTeams)
        file = os.path.join(directory, "results", "learnedBounds", "_" + tag + "0.csv")
        lbounds = sU.readBounds(file, num_constrType, num_constr)
        aggr_bounds = sU.aggrBounds(lbounds, num_constrType, num_constr, constrMaxval)

        tmpDir = os.path.join(directory, "tmp")
        tmpResult = os.path.join(tmpDir, "learnedBounds")
        cU.buildDirectory(tmpDir)
        cU.removeCSVFiles(tmpDir)

        numsam = len(next(os.walk(os.path.join(soln, "test")))[2])

        # build numSam samples from the learned constraints
        sampler.generate_multi_dim_sample(num_teams=numTeams, num_md_per_cycle=num_Matchdays, numSam=numsam,
                                          numCycle=numCycle,
                                          bounds=aggr_bounds,
                                          directory=tmpDir)

        # provide aggr bounds
        recall = calculateRecallFromFile(file=file, testsolndir=os.path.join(soln, "test"))
        precision = calculatePrecisionCorrect(model_bounds, tmpDir)
        #precision = calculatePrecisionFromSampleDir(model_bounds=model_bounds, sampledir=tmpDir)
        #precision_unbound = calculatePrecisionNonBounds(sampledir=tmpDir)
        #precision+=precision_unbound
        #precision/=2
        all_pre[seed] = precision
        all_rec[seed] = recall
        all_time[seed] = timeTaken
        row = []
        row.extend([numTeams])
        row.extend([numSam])
        row.extend([numSol])
        row.extend([recall])
        row.extend([precision])
        row.extend([timeTaken])

        detCsvWriter.writerow(row)
        print(row)

    row = []
    row.extend([numTeams])
    row.extend([numSam])
    row.extend([numSol])
    row.extend([sum(all_pre) / numSeed])
    row.extend([np.std(all_pre) / np.sqrt(numSeed)])
    row.extend([sum(all_rec) / numSeed])
    row.extend([np.std(all_rec) / np.sqrt(numSeed)])
    row.extend([sum(all_time) / numSeed])
    row.extend([np.std(all_time) / np.sqrt(numSeed)])
    csvWriter.writerow(row)
detcsv.close()
mycsv.close()
