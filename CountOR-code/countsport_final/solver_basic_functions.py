import os
import shutil
import time
import random

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


def generate4DSamples(numTeams, numSam, numCycles, sampleDir, mbounds):
    '''
    Generates a numSam of solutions for the sport scheduling problem with numTeams teams and stores them in sampleDir
    :param numTeams: Number of teams for the SSP
    :param numSam: Number of samples to generate
    :param numCycles: number of cycles in the ssp
    :param sampleDir: directory where the generated samples end up in
    :param mbounds:
    '''
    print("Generating " + str(numSam) + " samples for " + str(numTeams) + "teams and " + str(
        numCycles) + " cycles teams from Gurobi")
    start = time.clock()
    cU.buildDirectory(sampleDir)
    cU.removeCSVFiles(sampleDir)
    sampler.generate_multi_dim_sample(bounds=mbounds, directory=sampleDir, num_teams=numTeams,
                                      num_md_per_cycle=sU.calculateMatchDaysPerCycle(numTeams), numSam=numSam,
                                      numCycle=numCycles)
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



