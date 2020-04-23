import csv
import glob
import os

import numpy as np
from collections import OrderedDict


def readCSV(fileName):
    with open(fileName, 'rU') as csvFile:
        reader = csv.reader(csvFile, delimiter=',')
        data = list(reader)
        data = np.asarray(data)
        return data


def removeCSVFiles(dir):
    for fl in glob.glob(dir + "/*.csv"):
        os.remove(fl)


def buildDirectory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


# function strips csvdata from unnecessary noise/data fields with no data in them
# returns clean data tensor + variable arry
def cleanData(data):
    variables = []
    rows, cols = data.shape
    #     finding number of variables
    blankRows = 0
    while not data[blankRows, 0]:
        blankRows += 1
    blankCols = 0
    while not data[0, blankCols]:
        blankCols += 1
    for i in range(blankRows):
        variables.append(list(OrderedDict.fromkeys(data[i, blankCols:])))
    for i in range(blankCols):
        variables.append(list(OrderedDict.fromkeys(data[blankRows:, i])))
    variables_mat = np.matrix(variables)

    lengths = []
    for i in range(variables_mat.shape[1]):
        lengths.append(len(variables_mat[0, i]))
    dataTensor = np.zeros(lengths)

    for i in range(blankRows, rows):
        for j in range(blankCols, cols):
            if data[i, j].astype(int) == 1:
                index = ()
                for k in range(blankRows):
                    index = index + (variables[k].index(data[k, j]),)
                for k in range(blankCols):
                    index = index + (variables[blankRows + k].index(data[i, k]),)
                dataTensor[index] = 1
    return dataTensor, variables
