import numpy as np

a = [list(['1', '2']), list(['4', '5', '6']), list(['7', '8', '9'])]
trans = np.transpose(a)
trans2 = [*zip(*a)]

print(trans)
print(trans2)