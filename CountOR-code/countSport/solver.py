"""entry point: the solver tries to solve the sport scheduling proble,"""
import glob
import os
import sys
import time
from countSport import solverUtils as sU
from countSport import countor


# region vars
numSam = int(sys.argv[1])
numTeams = int(sys.argv[2])
tag = str(numTeams)+"_"+str(numSam)
# TODO ask
num_constrType = 12
num_constr = 6

# endregion

# Build directory structure for results and open up the files
directory = os.getcwd() + '/data/' + tag
if not os.path.exists(directory):
    os.makedirs(directory)
my_csv, csvWriter = sU.openMainCsv(directory)
det_csv, detCsvWriter = sU.openDetCsv(directory)

soln = os.path.join(directory ,"solutions")
result = os.path.join(directory,"results","learnedBounds")

if not os.path.exists(soln):
    os.makedirs(soln)
if not os.path.exists(result):
    os.makedirs(result)






print("Generating " + str(numSam) + " samples for " + str(numTeams)+" from Java api")
start = time.clock()
# TODO pull this from a port or make it in a sampler.py file
print("Generated ", numSam, " samples in ", time.clock() - start, " secs")

# clear the learned constraints
for fl in glob.glob(result + "/*.csv"):
    os.remove(fl)

start = time.clock()
countor.learnConstraintsForAll(directory,numTeams)
timeTaken = time.clock() - start
print("\nLearned bounds for ", numSam, " samples in ", timeTaken, ' secs')

tag = "Amt_T" + str(numTeams)
file = result + "/learnedBounds" + "_" + tag + "0.csv"
lbounds = sU.readBounds(file, num_constrType, num_constr)
