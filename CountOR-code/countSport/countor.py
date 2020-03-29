import glob
import os
import csv
import numpy as np
import time
from countSport import countorUtils as cU
from countSport import constraintFormulation as cF


def learnConstraintsForAllDir(directory,num_teams,output):
    start = time.clock()
    tag = "Amt_T" + str(num_teams)
    ind = 0
    for file in glob.glob(directory+'/*.csv'):
        data = cU.readCSV(file)
        dataTensor, variables = cU.cleanData(data)
        lenVar = []

        for i in range(len(variables)):
            lenVar.append(len(variables[i]))

        if ind == 0:
            saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))
        ind = 1
        saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))
    return time.clock()-start

def learnConstraintsForAll(directory,sampled_files, teamAmt,output):
    tag = str(len(sampled_files))+"Amt_T" + str(teamAmt)

    ind = 0
    for file in sampled_files:
        file2 = (os.path.join(directory,file))
        data = cU.readCSV(file2)
        dataTensor, variables = cU.cleanData(data)
        lenVar = []

        for i in range(len(variables)):
            lenVar.append(len(variables[i]))

        if ind == 0:
            saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))
        ind = 1
        saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))



def saveConstraintsForAll(dataTensor, variables, indicator, directory, tag,orderingNotImp=[2,3]):
    repeatDim = ()
    rep = set([variable for variable in range(len(variables)) if variable not in repeatDim])
    subsets = cF.split(rep, (), repeatDim)
    concatdir = directory
    if indicator == 0:
        cU.buildDirectory(concatdir)
        cU.removeCSVFiles(concatdir)

    with open(os.path.join(concatdir, "_" + tag + ".csv"), "a",newline='') as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=',')
        if indicator == 0:
            row = ([''] * 2)
            for subset in subsets:
                row.extend(subset)
                row.extend([''] * 5)
            csvWriter.writerow(row)

        else:
            row = []
            for l in range(len(subsets)):
                subset = subsets[l]
                newset = subset[0] + subset[1]
                # this value is used to filter max constraints
                maxPossible = 1
                for i in range(len(subset[1])):
                       maxPossible *= len(variables[subset[1][i]])
                idTensor = cF.tensorIndicator(dataTensor, newset, variables)
                sumSet = range(len(subset[0]), len(newset))

                sumTensor_max, sumTensor_min = cF.tensorSum(idTensor, sumSet, np.array(variables)[list(newset)], 0)
                # row.extend([sumTensor_min,sumTensor_max])
                # filter all the max poss values out (trivial constraints for everything)

                if sumTensor_min == maxPossible or sumTensor_min == 0:
                    row.extend([''])
                else:
                    row.extend([sumTensor_min])
                if sumTensor_max == maxPossible or sumTensor_max == 0:
                    row.extend([''])
                else:
                    row.extend([sumTensor_max])

                # first filter base on orderingNotImp
                if len(set(subset[1])) == 1 and len(set(orderingNotImp) & set(subset[1])) == 0:
                # second filter based on the (0,)(x,) constraints who are useles for us
                    if not(len(newset)==2 and newset[1]== 1):
                        minConsZero, maxConsZero, minConsNonZero, maxConsNonZero = cF.tensorConsZero(idTensor, sumSet,np.array(variables)[list(newset)])
                        #row.extend([minConsZero,maxConsZero,minConsNonZero,maxConsNonZero])
                        if minConsZero == maxPossible or minConsZero == 0:
                              row.extend([''])
                        else:
                             row.extend([minConsZero])
                        if maxConsZero == maxPossible or maxConsZero == 0:
                             row.extend([''])
                        else:
                             row.extend([maxConsZero])
                        if minConsNonZero == maxPossible or minConsNonZero == 0:
                             row.extend([''])
                        else:
                             row.extend([minConsNonZero])
                        if maxConsNonZero == maxPossible or maxConsNonZero == 0:
                            row.extend([''])
                        else:
                            row.extend([maxConsNonZero])
                    else:
                        row.extend(['']*4)
                else:
                    # when we dont capture the max cons sequence, we extend the set by four whitespaces
                    row.extend([''] * 4)

                row.extend([''])
            csvWriter.writerow(row)
