"""Util methods used by countsport_solver.py"""
import csv
import math
import os
import time

import numpy as np

from countsport_final import countsport_utils as cU
from countsport_final import multi_dimensional_sampler as sampler

"""
Opens csv and returns the writer 
"""


def openMainCsv(directory):
    my_csv = open(directory + "/results.csv", "w+", newline='')
    csvWriter = csv.writer(my_csv, delimiter=',')
    row = ['Teams', 'Sample', 'Soln', 'Precision', 'Precision_err', 'Recall', 'Recall_err', 'Time', 'Time_err']
    csvWriter.writerow(row)
    return my_csv, csvWriter



"""Determined results"""


def openDetCsv(directory):
    det_csv = open(directory + "/det_results.csv", "w+", newline='')
    detCsvWriter = csv.writer(det_csv, delimiter=',')
    row = ['Teams', 'Sample', 'numSol', 'Precision', 'Recall','TimeToLearn']
    detCsvWriter.writerow(row)
    return det_csv, detCsvWriter


def read3dBounds(file,num_constrType, num_constr):
        data = cU.readCSV(file)
        newlist = []
        for list2 in data:
            if list2 != []:
                newlist.append(list2)
        # transpose function of the tensor
        data_transpose = list(map(list, zip(*newlist)))
        # build array of len datatranspose by len datatranspose[0]-1
        data_int = np.zeros([len(data_transpose), len(data_transpose[0]) - 1])
        for i in range(len(data_transpose)):
            for j in range(1, len(data_transpose[i])):
                if data_transpose[i][j] != '':
                    data_int[i, j - 1] = int(data_transpose[i][j])
        bounds_tr = np.zeros([len(data_int[0]), num_constrType, num_constr])
        for j in range(len(data_int[0])):
            k = 0
            for i in range(83):
                if (i + 1) % 7 != 0:
                    bounds_tr[j, int(k / 6), k % 6] = data_int[i, j]
                    k += 1
        return bounds_tr.astype(np.int64)

def readBounds(file, num_constrType, num_constr):
    data = cU.readCSV(file)
    newlist = []
    for list2 in data:
        if list2 != []:
            newlist.append(list2)
    # transpose function of the tensor
    data_transpose = list(map(list, zip(*newlist)))
    # build array of len datatranspose by len datatranspose[0]-1
    data_int = np.zeros([len(data_transpose), len(data_transpose[0]) - 1])
    for i in range(len(data_transpose)):
        for j in range(1, len(data_transpose[i])):
            if data_transpose[i][j] != '':
                data_int[i, j - 1] = int(data_transpose[i][j])
    bounds_tr = np.zeros([len(data_int[0]), num_constrType, num_constr])
    for j in range(len(data_int[0])):
        k = 0
        for i in range(649):
            if (i + 1) % (num_constr+1) != 0:
                bounds_tr[j, int(k / num_constr), k % num_constr] = data_int[i, j]
                k += 1
    return bounds_tr.astype(np.int64)


"""Aggregates over the selected bounds to recalculate  """


def aggrBounds(selbounds, num_constrType, num_constr, constrMaxval=None):
    bounds_learned = np.zeros([num_constrType, num_constr])
    for i in range(num_constrType):
        for j in range(num_constr):
            row = int((i * num_constr + j) / num_constr)
            col = (i * num_constr + j) % num_constr
            if j % 2 == 0:
                bounds_learned[row, col] = np.min(selbounds[:, i, j])
            if j % 2 != 0:
                bounds_learned[row, col] = np.max(selbounds[:, i, j])
                if constrMaxval:
                    if bounds_learned[row, col] == constrMaxval[i]:
                        bounds_learned[row, col] = 0
    return bounds_learned.astype(np.int64)

def calculateMatchDaysPerCycle(numTeams):
    if numTeams % 2 == 0:
        return (numTeams - 1)
    else:
        return numTeams


def buildSolutionAndResultDirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    my_csv, csvWriter = openMainCsv(directory)
    det_csv, detCsvWriter = openDetCsv(directory)

    soln = os.path.join(directory, "solutions")
    result = os.path.join(directory, "results", "learnedBounds")

    if not os.path.exists(soln):
        os.makedirs(soln)
    if not os.path.exists(result):
        os.makedirs(result)

    return soln, result,csvWriter,detCsvWriter,det_csv,my_csv



def calculateBounds4D(amtTeams, amtCycles, actual_model_bounds,bk=False):
    # # number of constraint values we capture: minCount(0), maxCount(1), minConsZero(2), maxConsZero(3), minConsOne(4),
    # maxConsOne(5) tracemin (6) tracemax(7)  countplus_min(8) countplus_max(9) conszero_plus_min(10) conszero_plus_max(11)
    matchdays_per_cycle = calculateMatchDaysPerCycle(amtTeams)
    upperbound_hg_per_team = upperbound_ag_per_team = math.ceil((amtTeams-1)*amtCycles/2)
    lowerbound_hg_per_team = lowerbound_ag_per_team = math.floor((amtTeams-1)*amtCycles/2)
    upperbound_fixture_occuring = math.floor(amtCycles / 2) + amtCycles % 2
    lowerbound_fixture_occuring = 0
    lowerbound_total_games_per_day = upperbound_total_games_per_day = math.floor(amtTeams / 2)
    cycle_home_upper_bound = cycle_away_upper_bound =  math.ceil((amtTeams-1) / 2)
    cycle_home_lower_bound = cycle_away_lower_bound = math.floor((amtTeams-1) / 2)
    #cycle_away_upper_bound = amtTeams / 2 + amtTeams % 2
    #cycle_away_lower_bound = amtTeams / 2 - 1

    actual_model_bounds[6, 0] = lowerbound_total_games_per_day * matchdays_per_cycle
    actual_model_bounds[6, 1] = upperbound_total_games_per_day * matchdays_per_cycle
    actual_model_bounds[6,6] = 0
    actual_model_bounds[6,7] = 0
    actual_model_bounds[13,6] = 0
    actual_model_bounds[13,7] = 0
    actual_model_bounds[20,0] = lowerbound_hg_per_team
    actual_model_bounds[20,1] = upperbound_hg_per_team
    actual_model_bounds[20,6] = 0
    actual_model_bounds[20,7] = 0

    actual_model_bounds[27,0] = lowerbound_ag_per_team
    actual_model_bounds[27,1] = upperbound_ag_per_team

    actual_model_bounds[28, 0] = lowerbound_total_games_per_day
    actual_model_bounds[28, 1] = upperbound_total_games_per_day
    actual_model_bounds[29, 0] = lowerbound_total_games_per_day
    actual_model_bounds[29, 1] = upperbound_total_games_per_day
    actual_model_bounds[30, 0] = lowerbound_total_games_per_day
    actual_model_bounds[30, 1] = upperbound_total_games_per_day
    actual_model_bounds[31, 0] = cycle_away_lower_bound
    actual_model_bounds[31, 1] = cycle_away_upper_bound
    actual_model_bounds[31,2] = 1
    actual_model_bounds[31,3] = 2
    actual_model_bounds[31,4] = 1
    actual_model_bounds[31,5] = 2
    actual_model_bounds[34, 0] = cycle_home_lower_bound
    actual_model_bounds[34, 1] = cycle_home_upper_bound
    actual_model_bounds[34,2] = 1
    actual_model_bounds[34,3] = 2
    actual_model_bounds[34,4] = 1
    actual_model_bounds[34,5] = 2
    actual_model_bounds[43, 0] = lowerbound_fixture_occuring
    actual_model_bounds[43, 1] = upperbound_fixture_occuring
    actual_model_bounds[46, 1] = 1
    actual_model_bounds[46,6] = 0
    actual_model_bounds[46,7] = 0
    actual_model_bounds[46,8] = 1
    actual_model_bounds[46,9] = 1
    actual_model_bounds[47, 1] = 1
    actual_model_bounds[47,6] = 0
    actual_model_bounds[47,7] = 0
    actual_model_bounds[47,8] = 1
    actual_model_bounds[47,9] = 1
    actual_model_bounds[48, 1] = 1
    actual_model_bounds[49, 1] = 1

    if bk:
        actual_model_bounds_sg0 = np.zeros([len(actual_model_bounds),len(actual_model_bounds[0])])
        #actual_model_bounds_sg0[31, 2] = 1
        #actual_model_bounds_sg0[31, 3] = 6
        #actual_model_bounds_sg0[31, 4] = 1
        #actual_model_bounds_sg0[31, 5] = 2

        actual_model_bounds_sg0[34, 0] = cycle_away_lower_bound
        actual_model_bounds_sg0[34, 1] = cycle_away_upper_bound
        actual_model_bounds_sg0[34,2] = 1
        actual_model_bounds_sg0[34,3] = 2
        actual_model_bounds_sg0[34,4] = 1
        actual_model_bounds_sg0[34,5] = 2


        actual_model_bounds_sg1 = np.zeros([len(actual_model_bounds),len(actual_model_bounds[0])])
        #actual_model_bounds_sg1[31, 2] = 1
        #actual_model_bounds_sg1[31, 3] = 6
        #actual_model_bounds_sg1[31, 4] = 1
        #actual_model_bounds_sg1[31, 5] = 2

        actual_model_bounds_sg1[34, 0] = cycle_away_lower_bound
        actual_model_bounds_sg1[34, 1] = cycle_away_upper_bound
        actual_model_bounds_sg1[34,2] = 1
        actual_model_bounds_sg1[34,3] = 2
        actual_model_bounds_sg1[34,4] = 1
        actual_model_bounds_sg1[34,5] = 2


        actual_model_bounds_home_sg0 = np.zeros([len(actual_model_bounds),len(actual_model_bounds[0])])
        actual_model_bounds_home_sg0[34,0] = cycle_home_lower_bound
        actual_model_bounds_home_sg0[34, 1] = cycle_home_upper_bound
        actual_model_bounds_home_sg0[34,2] = 1
        actual_model_bounds_home_sg0[34,3] = 2
        actual_model_bounds_home_sg0[34,4] = 1
        actual_model_bounds_home_sg0[34,5] = 2

        actual_model_bounds_home_sg1 = np.zeros([len(actual_model_bounds),len(actual_model_bounds[0])])
        actual_model_bounds_home_sg1[34,0] = cycle_home_lower_bound
        actual_model_bounds_home_sg1[34, 1] = cycle_home_upper_bound
        actual_model_bounds_home_sg1[34,2] = 1
        actual_model_bounds_home_sg1[34,3] = 2
        actual_model_bounds_home_sg1[34,4] = 1
        actual_model_bounds_home_sg1[34,5] = 2

        actual_model_bounds_sg0 = actual_model_bounds_sg0.astype(np.int64)
        actual_model_bounds_sg1 = actual_model_bounds_sg1.astype(np.int64)
        actual_model_bounds_home_sg0 = actual_model_bounds_home_sg0.astype(np.int64)
        actual_model_bounds_home_sg1 = actual_model_bounds_home_sg1.astype(np.int64)

        return actual_model_bounds,actual_model_bounds_sg0,actual_model_bounds_sg1,actual_model_bounds_home_sg0,actual_model_bounds_home_sg1
    return actual_model_bounds

def generate4DSamples(numTeams,numSam,numCycles,sampleDir,mbounds):
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + "teams and "+str(numCycles) +" cycles teams from Gurobi api")
    start = time.clock()
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    sampler.generate_multi_dim_sample(bounds=mbounds, directory=sampleDir, num_teams=numTeams,
                                      num_md_per_cycle=calculateMatchDaysPerCycle(numTeams),numSam=100,
                                      numCycle=numCycles)
    print("Generated ", numSam, " samples in ", time.clock() - start, " secs")

