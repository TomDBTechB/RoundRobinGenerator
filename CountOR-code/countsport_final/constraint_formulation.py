import numpy as np
import itertools as it

"""
Splits given dimensions
"""


def split(X, partSet, repeatDim):
    finalSet = ()
    if len(partSet) == 2:
        return finalSet
    if len(partSet) == 1:
        for i in range(1, len(X) + 1):
            lst = list(it.combinations(X, i))
            for j in range(len(lst)):
                finalSet = finalSet + ((partSet + (lst[j],)),)
        return finalSet
    for i in range(1, len(X)):
        lst = list(it.combinations(X, i))
        for j in range(len(lst)):
            s1 = tuple(set(lst[j] + repeatDim))
            s2 = [x for x in X if x not in s1]
            s1 = (s1,)
            finalSet += split(s2, s1, repeatDim)
    return finalSet


def tensorSum(X, dim, var):
    newdim = range(len(X.shape))
    newdim = list(set(newdim) - set(dim))
    dim = newdim
    outputMatSize = []
    outputMatLoop = ()
    for i in range(len(dim)):
        outputMatSize.append(len(var[dim[i]]))
        outputMatLoop += (range(len(var[dim[i]])),)
    outputTensor = np.zeros(outputMatSize)
    for multiIndex in it.product(*outputMatLoop):
        a = []
        dimension = len(X.shape)
        for i in range(dimension):
            a.append(slice(0, X.shape[i]))
        for i in range(len(dim)):
            a[dim[i]] = multiIndex[i]
        outputTensor[multiIndex] = np.sum(X[tuple(a)])
    #    plt.hist(outputTensor.ravel(),bins='auto')
    #    plt.show()
    return np.amax(outputTensor).astype(np.int64), np.amin(outputTensor).astype(np.int64)


def tensorTracing(X):
    number_of_dims = len(X.shape)
    tracevals = np.trace(X, axis1=number_of_dims - 1, axis2=number_of_dims - 2)
    return np.amin(tracevals).astype(int), np.amax(tracevals).astype(int)


def count_plus(id_tensor_orig, sumset, var_orig,id_comp,var_comp):
    count_one = tensor_sum(id_tensor_orig,sumset, var_orig)
    count_comp = tensor_sum(id_comp,sumset,var_comp)
    summed_dimension = count_one+count_comp
    return np.amin(summed_dimension).astype(int),np.amax(summed_dimension).astype(int)

def tensor_sum(X, dim, var):
    newdim = range(len(X.shape))
    newdim = list(set(newdim) - set(dim))
    dim = newdim
    outputMatSize = []
    outputMatLoop = ()
    for i in range(len(dim)):
        outputMatSize.append(len(var[dim[i]]))
        outputMatLoop += (range(len(var[dim[i]])),)
    outputTensor = np.zeros(outputMatSize)
    for multiIndex in it.product(*outputMatLoop):
        a = []
        dimension = len(X.shape)
        for i in range(dimension):
            a.append(slice(0, X.shape[i]))
        for i in range(len(dim)):
            a[dim[i]] = multiIndex[i]
        outputTensor[multiIndex] = np.sum(X[tuple(a)])
    return outputTensor





def tensorIndicator(X, dim, var):
    outputMatSize = []
    outputMatLoop = ()
    for i in range(len(dim)):
        outputMatSize.append(len(var[dim[i]]))
        outputMatLoop += (range(len(var[dim[i]])),)
    outputTensor = np.zeros(outputMatSize)
    for multiIndex in it.product(*outputMatLoop):
        a = []
        dimension = len(X.shape)
        for i in range(dimension):
            a.append(slice(0, X.shape[i]))
        for i in range(len(dim)):
            a[dim[i]] = multiIndex[i]
        if np.count_nonzero(X[tuple(a)]) != 0:
            outputTensor[multiIndex] = 1

    return outputTensor


def tensorConsZero(X, dim, var):
    newdim = range(len(X.shape))
    newdim = list(set(newdim) - set(dim))
    dim = newdim
    outputMatSize = []
    outputMatLoop = ()
    for i in range(len(dim)):
        outputMatSize.append(len(var[dim[i]]))
        outputMatLoop += (range(len(var[dim[i]])),)
    outputTensor1_min = np.zeros(outputMatSize)
    outputTensor2_min = np.zeros(outputMatSize)
    outputTensor1_max = np.zeros(outputMatSize)
    outputTensor2_max = np.zeros(outputMatSize)
    for multiIndex in it.product(*outputMatLoop):
        a = []
        dimension = len(X.shape)
        for i in range(dimension):
            a.append(slice(0, X.shape[i]))
        for i in range(len(dim)):
            a[dim[i]] = multiIndex[i]
        #        print(X[tuple(a)])
        outputTensor1_min[multiIndex] = minConsZero(X[tuple(a)])
        #        print(outputTensor1_min[multiIndex])
        outputTensor2_min[multiIndex] = minConsNonZero(X[tuple(a)])
        outputTensor1_max[multiIndex] = maxConsZero(X[tuple(a)])
        outputTensor2_max[multiIndex] = maxConsNonZero(X[tuple(a)])

    outputTensor1_min = outputTensor1_min[np.nonzero(outputTensor1_min)]
    outputTensor2_min = outputTensor2_min[np.nonzero(outputTensor2_min)]
    outputTensor1_max = outputTensor1_max[np.nonzero(outputTensor1_max)]
    outputTensor2_max = outputTensor2_max[np.nonzero(outputTensor2_max)]
    sz1, sz2, sz3, sz4 = 0, 0, 0, 0

    if outputTensor1_min.size > 0:
        sz1 = np.amin(outputTensor1_min).astype(np.int64)
    if outputTensor2_min.size > 0:
        sz2 = np.amin(outputTensor2_min).astype(np.int64)
    if outputTensor1_max.size > 0:
        sz3 = np.amax(outputTensor1_max).astype(np.int64)
    if outputTensor2_max.size > 0:
        sz4 = np.amax(outputTensor2_max).astype(np.int64)
    return sz1, sz3, sz2, sz4


def count_consecutive_set(X):
    prev_val = None
    indices = []
    for i in range(len(X)):
        if i == 0:
            prev_val = X[i]
            continue
        if prev_val != X[i]:
            indices.append(i)
            prev_val = X[i]
            continue
    splits = np.split(X, indices_or_sections=indices)
    filtered = list(filter(lambda x: x.size >= 2, splits))
    return len(filtered
               )


def minConsZero(X):
    #    print(X)
    mn = 1000
    ind = 0
    for i in range(len(X)):
        if np.count_nonzero(X[i]) == 0:
            ind += 1
        else:
            if ind > 0:
                mn = min(ind, mn)
            ind = 0
    if mn == 1000 or ind > 0:
        #    if mn==1000:
        return min(mn, ind)
    #    print(mn)
    return mn


def maxConsZero(X):
    mx = 0
    ind = 0
    for i in range(len(X)):
        if np.count_nonzero(X[i]) == 0:
            ind += 1
            mx = max(ind, mx)
        else:
            ind = 0
    return max(mx, ind)


def minConsNonZero(X):
    mn = 1000
    ind = 0
    for i in range(len(X)):
        if np.count_nonzero(X[i]) != 0:
            ind += 1
        else:
            if ind > 0:
                mn = min(ind, mn)
            ind = 0
    if mn == 1000 or ind > 0:
        #    if mn==1000:
        return min(mn, ind)
    return mn


def maxConsNonZero(X):
    mx = 0
    ind = 0
    for i in range(len(X)):
        if np.count_nonzero(X[i]) != 0:
            ind += 1
            mx = max(ind, mx)
        else:
            ind = 0
    return max(mx, ind)