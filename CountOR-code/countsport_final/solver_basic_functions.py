import csv
import os
import shutil
import time
import random

import pandas as pd
import numpy as np

from countor4d import solverUtils as sU
from countor4d import countorUtils as cU
from countsport_final import multi_dimensional_sampler as sampler


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


def readCSV(fileName):
    with open(fileName, 'rU') as csvFile:
        reader = csv.reader(csvFile, delimiter=',')
        data = list(reader)
        data = np.asarray(data)
        return data


def generate4DSamples(numTeams, numSam, numCycles, sampleDir, mbounds, unsolvable, lost_data, skill_group=None,
                      skillbounds0=None, skillbounds1=None):
    '''
    Generates a numSam of solutions for the sport scheduling problem with numTeams teams and stores them in sampleDir
    :param numTeams: Number of teams for the SSP
    :param numSam: Number of samples to generate
    :param numCycles: number of cycles in the ssp
    :param sampleDir: directory where the generated samples end up in
    :param mbounds:
    '''
    missed_cycle = False
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + "teams and " + str(
        numCycles) + " cycles teams from Gurobi")
    start = time.clock()
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    num_games_cycle = sU.calculateMatchDaysPerCycle(numTeams)
    sampler.generate_multi_dim_sample(bounds=mbounds, directory=sampleDir, num_teams=numTeams,
                                      num_md_per_cycle=sU.calculateMatchDaysPerCycle(numTeams), numSam=numSam,
                                      numCycle=numCycles, unlearnable=unsolvable, sk=skill_group, bounds0=skillbounds0,
                                      bounds1=skillbounds1)
    if lost_data:
        files = next(os.walk(sampleDir))[2]
        for idx, file in enumerate(files):
            random.seed(idx)
            file_path = os.path.join(sampleDir, file)
            data = readCSV(file_path)
            if missed_cycle:
                dropped = np.delete(data, np.s_[int((data.shape[1] + 1) / 2):data.shape[1]], axis=1)
                mirror = np.delete(dropped, 0, axis=1)
                mirror[0] = np.repeat('C1', mirror.shape[1])
                mirror[3:] = np.concatenate(np.split(np.transpose(mirror[3:]), num_games_cycle), axis=1)
                result = np.concatenate((dropped, mirror), axis=1)
                pd.DataFrame(result).to_csv(file_path, header=False, index=False)
            else:
                first_col = data[3:][:, 0]
                blocks = np.delete(data[3:], 0, axis=1)
                splitted = np.split(blocks, (num_games_cycle * 2), axis=1)
                idx1 = random.randint(0, (num_games_cycle * 2)-1)
                idx2 = random.randint(0, (num_games_cycle * 2)-1)
                if idx1 == idx2:
                    idx1 -= 1

                splitted[idx1], splitted[idx2] = splitted[idx2], splitted[idx1]
                newset = np.concatenate((splitted),axis=1)
                stack = np.column_stack((first_col,newset))
                data[3:] = stack
                pd.DataFrame(data).to_csv(file_path, header=False, index=False)

    print("Generated ", numSam, " samples in ", time.clock() - start, " secs")


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
