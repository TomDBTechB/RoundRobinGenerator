import os
import time

import numpy as np
import random

from countsport_final import solver_utils as sU
from countsport_final import countsport_utils as cU
from countsport_final import multi_dimensional_sampler as sampler
from countsport_final import countsport as countsport
from countsport_final.solver_basic_functions import buildSolutionAndResultDirs
from countsport_final.solver_basic_functions import generate4DSamples, randomSplit

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
        accept += check_constrained(sampled_bound=i, model_bound=aggregated_learned_bounds)
    return accept / len(recallBounds)


def calculatePrecision(model_bounds, sampledir, unsolvable):
    files = next(os.walk(sampledir))[2]
    sample_bound_file = os.path.join(tmpResult, "_" + str(len(files)) + "Amt_T" + str(numTeams) + "0.csv")
    learnConstraintsFromFiles(sampledir, files, tmpResult)
    precisionBounds = sU.readBounds(sample_bound_file, num_constrType, num_constr)

    accept = 0
    for i in range(precisionBounds.shape[0]):
        boundsval = check_constrained(precisionBounds[i], model_bounds)
        if unsolvable:
            unsolv_val = check_unsolvable(os.path.join(sampledir, files[i]))
            if boundsval+unsolv_val!=2:
                boundsval=0
            else:
                boundsval=1
        accept += boundsval
    return accept / len(files)


def check_unsolvable(file):
    data = cU.readCSV(file)
    data_tensor = cU.cleanData(data)[0]
    for c in range(len(data_tensor)):
        lower = len(data_tensor[0])-2
        upper = len(data_tensor[0])-1
        for r in range(lower,upper):
            if data_tensor[c][r][1][2]+data_tensor[c][r][2][1] != 0:
                return 1
    return 0


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





def learnConstraintsFromFiles(learndir, sampled_files, outputdir):
    start = time.clock()
    countsport.learnConstraintsForAll(learndir, sampled_files, numTeams, outputdir)
    timeTaken = time.process_time() - start
    return timeTaken


numSam = 100 # int(sys.argv[1])
numTeams = 8 # int(sys.argv[2])
numCycle = 2
num_Matchdays = sU.calculateMatchDaysPerCycle(numTeams)
solution_seed = [1, 5, 10, 25]
unsolvable = False
lost_data = True
tag = str(numCycle) + "_" + str(numTeams) + "_" + str(numSam)

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
num_constr = 12  # (count(2) conszero(2) consone(2) trace(2) countplus(2))

actual_model_bounds = np.zeros([num_constrType, num_constr])
model_bounds = sU.calculateBounds4D(amtTeams=numTeams, amtCycles=numCycle,
                                    actual_model_bounds=actual_model_bounds)
constrMaxval = []

dimSize = [numCycle, num_Matchdays, numTeams, numTeams]
for val in constrList:
    tot = 1
    for i in range(len(val[1])):
        tot *= dimSize[int(val[1][i])]
    constrMaxval.append(tot)

directory = os.path.join(os.getcwd(), "data", tag)
soln, result, prec, csvWriter, detCsvWriter, detcsv, mycsv = buildSolutionAndResultDirs(directory)

# generate the samples
generate4DSamples(mbounds=model_bounds, numTeams=numTeams, numSam=numSam, numCycles=numCycle, sampleDir=soln, unsolvable=unsolvable,lost_data=lost_data)
# split into 0.9 learn 0.1 testset
randomSplit(soln, 0.1)

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
        precision = calculatePrecision(model_bounds, tmpDir,unsolvable)


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
