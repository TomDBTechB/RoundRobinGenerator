"""Util methods used by solver.py"""
import math
import os
import shutil
from random import random

from countSport import countorUtils as cU
import numpy as np
import csv
from subprocess import *
import time
from countSport import multi_dimensional_sampler as sampler


"""
Opens csv and returns the writer 
"""


def openMainCsv(directory):
    my_csv = open(directory + "/results.csv", "w+", newline='')
    csvWriter = csv.writer(my_csv, delimiter=',')
    row = ['Teams', 'Sample', 'Soln', 'Precision', 'Precision_err', 'Recall', 'Recall_err', 'Time', 'Time_err']
    csvWriter.writerow(row)
    return my_csv, csvWriter


"""
Makes jar callable from the source code 
"""


def jarWrapper(*args):
    process = Popen(['java', '-jar'] + list(args), stdout=PIPE, stderr=PIPE)
    while process.poll() is None:
        line = process.stdout.readline().decode("utf-8")
        if line != '' and '\n':
            print(line)
    stdout, stderr = process.communicate()
    for line in stdout:
        decode = line.decode("utf-8")
        if decode != '' and '\n':
            print(decode)
    if stderr is not None:
        for line in stderr:
            decode = line.decode("utf-8")

            if decode != '' and '\n' and None:
                print(decode)


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
        for i in range(349):
            if (i + 1) % 7 != 0:
                bounds_tr[j, int(k / 6), k % 6] = data_int[i, j]
                k += 1
    return bounds_tr.astype(np.int64)


"""Aggregates over the selected bounds to recalculate  """


def aggrBounds(selbounds, num_constrType, num_constr, constrMaxval):
    bounds_learned = np.zeros([num_constrType, num_constr])
    for i in range(num_constrType):
        for j in range(num_constr):
            row = int((i * num_constr + j) / 6)
            col = (i * num_constr + j) % 6
            if j % 2 == 0:
                bounds_learned[row, col] = np.min(selbounds[:, i, j])
            if j % 2 != 0:
                bounds_learned[row, col] = np.max(selbounds[:, i, j])
                if bounds_learned[row, col] == constrMaxval[i]:
                    bounds_learned[row, col] = 0
    return bounds_learned.astype(np.int64)


###########checks if bound2 is more constrained than bound1##################
def moreConstrained(bound1, bound2, num_constrType, num_constr):
    output = 1
    for i in range(num_constrType):
        for j in range(num_constr):
            if bound1[i, j] == 0:
                continue
            if j % 2 == 0 and bound2[i, j] < bound1[i, j]:
                print(bound2[i,j])
                print(bound1[i,j])
                output = 0
                break
            if j % 2 == 1 and bound2[i, j] > bound1[i, j]:
                output = 0
                break
            if j % 2 == 1 and bound2[i, j] == 0 and bound1[i, j] > 0:
                output = 0
                break
        if output == 0:
            break
    return output


def calculateMatchDaysPerCycle(numTeams):
    if numTeams % 2 == 0:
        return (numTeams - 1)
    else:
        return numTeams

def calculateMatchDays(numTeams):
        if numTeams % 2 == 0:
            return (numTeams - 1)*2
        else:
            return numTeams*2

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

def calculateBounds4D(amtTeams, amtCycles, actual_model_bounds):
    # # number of constraint values we capture: minCount(0), maxCount(1), minConsZero(2), maxConsZero(3), minConsOne(4), maxConsOne(5)
    matchdays_per_cycle = calculateMatchDaysPerCycle(amtTeams)
    upperbound_hg_per_team = upperbound_ag_per_team = math.ceil((amtTeams-1)*amtCycles/2)
    lowerbound_hg_per_team = lowerbound_ag_per_team = math.floor((amtTeams-1)*amtCycles/2)
    upperbound_fixture_occuring = math.floor(amtCycles / 2) + amtCycles % 2
    lowerbound_fixture_occuring = 0
    lowerbound_total_games_per_day = upperbound_total_games_per_day = math.floor(amtTeams / 2)
    cycle_home_upper_bound = amtTeams / 2 + amtTeams % 2
    cycle_home_lower_bound = amtTeams / 2 - 1
    cycle_away_upper_bound = amtTeams / 2 + amtTeams % 2
    cycle_away_lower_bound = amtTeams / 2 - 1


    actual_model_bounds[6, 0] = lowerbound_total_games_per_day * matchdays_per_cycle
    actual_model_bounds[6, 1] = upperbound_total_games_per_day * matchdays_per_cycle
    actual_model_bounds[20,0] = lowerbound_hg_per_team
    actual_model_bounds[20,1] = upperbound_hg_per_team
    actual_model_bounds[20,4] = 1
    actual_model_bounds[20,5] = 2
    actual_model_bounds[27,0] = lowerbound_ag_per_team
    actual_model_bounds[27,1] = upperbound_ag_per_team
    actual_model_bounds[31,4] = 1
    actual_model_bounds[31,5] = 2
    actual_model_bounds[28, 0] = lowerbound_total_games_per_day
    actual_model_bounds[28, 1] = upperbound_total_games_per_day
    actual_model_bounds[29, 0] = lowerbound_total_games_per_day
    actual_model_bounds[29, 1] = upperbound_total_games_per_day
    actual_model_bounds[30, 0] = lowerbound_total_games_per_day
    actual_model_bounds[30, 1] = upperbound_total_games_per_day
    actual_model_bounds[31, 0] = cycle_away_lower_bound
    actual_model_bounds[31, 1] = cycle_away_upper_bound
    actual_model_bounds[34, 0] = cycle_home_lower_bound
    actual_model_bounds[34, 1] = cycle_home_upper_bound
    actual_model_bounds[43, 0] = lowerbound_fixture_occuring
    actual_model_bounds[43, 1] = upperbound_fixture_occuring
    actual_model_bounds[46, 1] = 1
    actual_model_bounds[47, 1] = 1
    actual_model_bounds[48, 1] = 1
    actual_model_bounds[49, 1] = 1

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

