import glob
import os
import csv
import numpy as np

from countSport import countorUtils as cU
from countSport import constraintFormulation as cF



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



# def learnConstraintsForAll(directory, teamAmt):
#     tag = "Amt_T" + str(teamAmt)
#
#     ind = 0
#     for file in glob.glob(os.path.join(directory,"solutions","*.csv")):
#         data = cU.readCSV(file)
#         dataTensor, variables = cU.cleanData(data)
#         lenVar = []
#
#         for i in range(len(variables)):
#             lenVar.append(len(variables[i]))
#
#         if ind == 0:
#             saveConstraintsForAll(dataTensor, variables, ind, directory, tag + str(0))
#         ind = 1
#         saveConstraintsForAll(dataTensor, variables, ind, directory, tag + str(0))


def saveConstraintsForAll(dataTensor, variables, indicator, directory, tag):
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
                row.extend([sumTensor_min])
                row.extend([sumTensor_max])

                if len(set(subset[1])) == 1 and len(set(subset[1])) == 0:
                    minConsZero, maxConsZero, minConsNonZero, maxConsNonZero = cF.tensorConsZero(idTensor, sumSet,
                                                                                                 learnConstraintsForAll(
                                                                                                     os.getcwd(), 6))
                    row.extend([minConsZero])
                    row.extend([maxConsZero])
                    row.extend([minConsNonZero])
                    row.extend([maxConsNonZero])
                else:
                    row.extend([''] * 4)
                row.extend([''])
            csvWriter.writerow(row)

