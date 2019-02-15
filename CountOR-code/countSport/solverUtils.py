"""Util methods used by solver.py"""

from countSport import countorUtils as cU
import numpy as np
import csv

def openMainCsv(directory):
    my_csv = open(directory + "/results.csv", "w+")
    csvWriter = csv.writer(my_csv, delimiter=',')
    row = ['Nurses', 'Sample', 'Soln', 'Precision', 'Precision_err', 'Recall', 'Recall_err', 'Time', 'Time_err']
    csvWriter.writerow(row)
    return my_csv,csvWriter

"""Determined results"""
def openDetCsv(directory):
    det_csv = open(directory + "/det_results.csv", "w+")
    detCsvWriter = csv.writer(det_csv, delimiter=',')
    row = ['Nurses', 'Sample', 'Soln', 'Seed', 'Precision', 'Recall', 'Time']
    detCsvWriter.writerow(row)
    return det_csv,detCsvWriter



def readBounds(file, num_constrType, num_constr):
    data = cU.readCSV(file)
    # transpose function of the tensor
    data_transpose = list(zip(*data))
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
1
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
