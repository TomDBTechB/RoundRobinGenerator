import glob
import os
import csv
import numpy as np
import time
from countor4d import countorUtils as cU
from countsport_final import constraint_formulation as cF

'''
def learnConstraintsForAllDir(directory, num_teams, output):
    start = time.clock()
    tag = "Amt_T" + str(num_teams)
    ind = 0
    for file in glob.glob(directory + '/*.csv'):
        data = cU.readCSV(file)
        dataTensor, variables = cU.cleanData(data)
        lenVar = []

        for i in range(len(variables)):
            lenVar.append(len(variables[i]))

        if ind == 0:
            saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))
        ind = 1
        saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))
    return time.clock() - start
'''

def learnConstraintsForAll(directory, sampled_files, teamAmt, output,info=None,bk=False):
    tag = str(len(sampled_files)) + "Amt_T" + str(teamAmt)

    ind = 0
    for file in sampled_files:
        file2 = (os.path.join(directory, file))
        data = cU.readCSV(file2)
        dataTensor, variables = cU.cleanData(data)
        lenVar = []

        for i in range(len(variables)):
            lenVar.append(len(variables[i]))

        if ind == 0:
            saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))
            saveConstraintsForAll(dataTensor,variables,1,output,tag+str(0))
        else:
            saveConstraintsForAll(dataTensor, variables, ind, output, tag + str(0))

        if bk:
            strengthgroup = np.zeros([2,teamAmt])
            strengthgroup[0] = info
            strengthgroup[1] = [int(x==0) for x in info]
            # ind = 0

            for f in range(2):
                if f==0:
                    tmp = info
                else:
                    tmp = [int(x==0) for x in info]
                strengthgroup = np.zeros([teamAmt,int(sum(tmp))])
                k=0
                for j in range(len(tmp)):
                    if tmp[j] == 1:
                        strengthgroup[j][k] = 1
                        k+=1
                dim=3 # refers to the home dimension
                updated_vars = variables[:]
                updated_vars[dim] = [x for x, y in zip(variables[dim],tmp) if y==1]
                mat = np.tensordot(dataTensor,strengthgroup,[dim,0])
                if ind==0:
                    saveConstraintsForAll(dataTensor=mat,variables=updated_vars,indicator=0,directory=output,tag=tag+str(0)+str(f))
                    saveConstraintsForAll(dataTensor=mat,variables=updated_vars,indicator=1,directory=output,tag=tag+str(0)+str(f))
                else:
                    saveConstraintsForAll(dataTensor=mat,variables=updated_vars,indicator=ind,directory=output,tag=tag+str(0)+str(f))
        ind=1

def saveConstraintsForAll(dataTensor, variables, indicator, directory, tag, orderingNotImp=[2, 3]):
    repeatDim = ()
    rep = set([variable for variable in range(len(variables)) if variable not in repeatDim])
    subsets = cF.split(rep, (), repeatDim)
    concatdir = directory
    if indicator == 0 and tag[-2] !='0':
        cU.buildDirectory(concatdir)
        cU.removeCSVFiles(concatdir)

    with open(os.path.join(concatdir, "_" + tag + ".csv"), "a", newline='') as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=',')
        # First run in this script provides the header row
        if indicator == 0:
            row = ([''] * 2)
            for subset in subsets:
                row.extend(subset)
                row.extend([''] * 11)
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

                sumTensor_max, sumTensor_min = cF.tensorSum(idTensor, sumSet, np.array(variables)[list(newset)])
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

                # first filter base on orderingNotImpd
                if len(set(subset[1])) == 1 and len(set(orderingNotImp) & set(subset[1])) == 0:
                    # second filter based on the (0,)(x,) constraints who are useles for us and filter constraints with
                    # all the dimensions involved in |D|, also filter everything out with orderingnotImp completely in S
                    # also filter everything out with cycle ordering in M, since this also is irrelevant to us
                    if not (len(newset) == 2 and newset[1] == 1) and not (len(newset) == len(rep)) and not (
                            subset[0] == tuple(orderingNotImp)) and not (subset[1] == 0):
                        minConsZero, maxConsZero, minConsNonZero, maxConsNonZero = cF.tensorConsZero(idTensor, sumSet,
                                                                                                     np.array(
                                                                                                         variables)[
                                                                                                         list(newset)])
                        # row.extend([minConsZero,maxConsZero,minConsNonZero,maxConsNonZero])
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
                        # row.extend(['']*4)
                    else:
                        row.extend([''] * 4)
                else:
                    # when we dont capture the max cons sequence, we extend the set by four whitespaces
                    row.extend([''] * 4)
                if (idTensor.shape[len(newset) - 1] == idTensor.shape[len(newset) - 2]) & (len(newset) == len(rep)):
                    # first filter, see that the last 2 dimension are of equal length
                    # second filter, see that M and S contain all the dimensions in D
                    tracing_min, tracing_max = cF.tensorTracing(idTensor)
                    row.extend([tracing_min, tracing_max])
                else:
                    row.extend([''] * 2)

                # filter: newset = |D|, |M|=1, |S| = |D|-1 + having a swapping length + make sure last 2 dimension of id tensor are equal
                if (len(newset) == len(rep)) & (len(subset[0]) == len(rep) - 1) & (len(subset[1]) == 1) & (
                        subset[1][0] == 2 or subset[1][0] == 3) & (idTensor.shape[-1] == idTensor.shape[-2]):
                    # paraamterize this
                    comp_newset = (newset[0], newset[1], newset[-1], newset[-2])
                    id_tensor_comp = cF.tensorIndicator(dataTensor, comp_newset, variables)

                    countplus_min, count_plus_max = cF.count_plus(id_tensor_orig=idTensor, sumset=sumSet,
                                                                  var_orig=np.array(variables)[list(newset)],
                                                                  id_comp=id_tensor_comp,
                                                                  var_comp=np.array(variables)[list(comp_newset)])

                    row.extend([countplus_min, count_plus_max])
                else:
                    row.extend([''] * 2)

                if False:
                    between_games_min, between_games_max = 0, 0
                    row.extend([between_games_min, between_games_max])
                else:
                    row.extend([''] * 2)

                row.extend([''])
            csvWriter.writerow(row)
